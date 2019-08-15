#encoding: utf-8

import json
import os
import re
from urllib.parse import quote

import terminado
import tornado
from ipython_genutils.py3compat import which
from notebook.base.handlers import IPythonHandler
from notebook.prometheus.metrics import TERMINAL_CURRENTLY_RUNNING_TOTAL
from notebook.terminal import api_handlers
from notebook.terminal.handlers import TerminalHandler, TermSocket
from notebook.utils import url_path_join as ujoin
from terminado import NamedTermManager
from tornado import web
from tornado.log import app_log

__version__ = "1.0.0"


def _jupyter_server_extension_paths():
    return [{
        "module": "jupyter_expanded_terminal"
    }]


def _jupyter_nbextension_paths():
    return [dict(
        section="common",
        src="static",
        dest="expanded_terminal",
        require="expanded_terminal/main"
    )]


class TerminalExtensionHandler(IPythonHandler):

    @web.authenticated
    def get(self):
        self.finish(json.dumps({"version": __version__}))


class TerminalHandler(TerminalHandler):

    @web.authenticated
    def get(self, term_name):
        # encode `term_name` to support more characters
        term_name = quote(term_name)
        super(TerminalHandler, self).get(term_name)


class APITerminalRootHandler(api_handlers.TerminalRootHandler):

    @web.authenticated
    def post(self):
        """POST /terminals creates a new terminal and redirects to it"""
        tm = self.terminal_manager
        notebook_dir = tm.extra_env["JUPYTER_SERVER_ROOT"]
        dat = tornado.escape.json_decode(self.request.body)

        # cwd of new terminal
        cwd = os.path.join(notebook_dir, dat.get("cwd", ""))
        # name of new terminal (show on web page)
        name = dat.get("name", "").strip()
        # the command to run in the new terminal after startup
        startup_command = dat.get("startup_command", [])
        if not isinstance(startup_command, list):
            startup_command = []
        startup_command = [str(x).strip() for x in startup_command]
        startup_command = [x for x in startup_command if x]
        startup_command = "\r\n".join(startup_command) + "\r\n"

        if any([term_name == name for term_name in tm.terminals]):
            raise web.HTTPError(409, "Terminal already exists")
        else:
            tm.term_settings["cwd"] = cwd
            if name:
                term = tm.get_terminal(name)
                term.ptyproc.write(startup_command)
            else:
                name, term = tm.new_named_terminal()
                term.ptyproc.write(startup_command)
            tm.term_settings["cwd"] = None
            self.finish(json.dumps({"name": name}))

        # Increase the metric by one because a new terminal was created
        TERMINAL_CURRENTLY_RUNNING_TOTAL.inc()


class APITerminalHandler(api_handlers.TerminalHandler):
    SUPPORTED_METHODS = ("GET", "POST", "DELETE")

    @web.authenticated
    def post(self, name):
        """rename terminal"""
        tm = self.terminal_manager
        if name in tm.terminals:
            # the new terminal name to be used
            new_name = self.get_argument("new_name", "").strip()
            if not new_name or new_name == name:
                return self.finish(json.dumps({"name": name}))
            if any([term_name == new_name for term_name in tm.terminals]):
                raise web.HTTPError(409, "Terminal already exists")
            term = tm.terminals[name]
            term.term_name = new_name
            tm.terminals[new_name] = term
            del tm.terminals[name]
            return self.finish(json.dumps({"name": new_name}))
        else:
            raise web.HTTPError(404, "Terminal not found: %r" % name)


def initialize(webapp, notebook_dir, connection_url, settings):
    # remove existing terminal web handlers
    for host_rule in webapp.default_router.rules:
        if not hasattr(host_rule.matcher, "host_pattern"):
            continue
        if host_rule.matcher.host_pattern.pattern != ".*$":
            continue
        new_rules = []
        for path_rule in host_rule.target.rules:
            if not hasattr(path_rule.matcher, "regex"):
                continue
            pattern = path_rule.matcher.regex.pattern
            if pattern.find("/terminals/") == -1 and not pattern.endswith("/terminals$"):
                new_rules.append(path_rule)
        host_rule.target.rules = new_rules

    if os.name == "nt":
        default_shell = "powershell.exe"
    else:
        default_shell = which("sh")
    shell = settings.get(
        "shell_command",
        [os.environ.get("SHELL") or default_shell]
    )

    if os.name != "nt":
        shell.append("-l")
    terminal_manager = webapp.settings["terminal_manager"] = NamedTermManager(
        shell_command=shell,
        extra_env={
            "JUPYTER_SERVER_ROOT": notebook_dir,
            "JUPYTER_SERVER_URL": connection_url,
        },
    )
    terminal_manager.log = app_log
    base_url = webapp.settings["base_url"]
    handlers = [
        (ujoin(base_url, r"/terminals/([^/]+)"), TerminalHandler),
        (ujoin(base_url, r"/terminals/websocket/([^/]+)"), TermSocket,
         {"term_manager": terminal_manager}),
        (ujoin(base_url, r"/api/terminals"), APITerminalRootHandler),
        (ujoin(base_url, r"/api/terminals/([^/]+)"), APITerminalHandler),
        (ujoin(base_url, r"/terminal_extension"), TerminalExtensionHandler),
    ]
    webapp.add_handlers(".*$", handlers)


def load_jupyter_server_extension(jupyter_app):
    if not jupyter_app.terminals_enabled:
        return

    web_app = jupyter_app.web_app
    notebook_dir = jupyter_app.notebook_dir
    connection_url = jupyter_app.connection_url
    terminado_settings = jupyter_app.terminado_settings

    initialize(web_app, notebook_dir, connection_url, terminado_settings)
    web_app.settings["terminals_available"] = True
