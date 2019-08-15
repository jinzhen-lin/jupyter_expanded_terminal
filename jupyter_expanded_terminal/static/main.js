define([
    "jquery",
    "tree/js/terminallist",
    "base/js/dialog",
    "base/js/namespace",
    "base/js/utils",
    "base/js/keyboard",
    "services/config"
], function($, terminallist, dialog, IPython, utils, keyboard, configmod) {
    var base_url = $("body").data("baseUrl");
    var config = new configmod.ConfigSection('common', {
        base_url: base_url
    });

    // define default values for config parameters
    var params = {
        expanded_terminal_custom_name: true,
        expanded_terminal_switch_cwd: true,
        expanded_terminal_startup_command: [""],
    };

    // update params with any specified in the server's config file
    config.loaded.then(function() {
        for (var key in params) {
            if (config.data.hasOwnProperty(key))
                params[key] = config.data[key];
        }
    });

    function input_terminal_name_dialog(button_name, click_function) {
        var create_msg = "Enter a new terminal name:";
        var input = $("<input/>").attr("type", "text")
            .attr("size", "25").attr("aria-labelledby", "create-message")
            .addClass("form-control").val("");
        var dialog_body = $("<div/>").append(
            $("<p/>").addClass("create-message")
            .attr("id", "create-message").text(create_msg)
            .append($("<br/>")).append(input)
        );
        var buttons = {
            Cancel: {},
        };
        buttons[button_name] = {
            class: "btn-primary",
            click: click_function
        };
        var d = dialog.modal({
            title: "New Terminal",
            body: dialog_body,
            default_button: "Cancel",
            buttons: buttons,
            open: function() {
                input.keydown(function(event) {
                    if (event.which === keyboard.keycodes.enter) {
                        d.find(".btn-primary").first().click();
                        return false;
                    }
                });
                input.focus();
            }
        });
    }

    function expand_new_terminal() {
        var TerminalList = terminallist.TerminalList;
        TerminalList.prototype.new_terminal = function(event) {
            if (event) {
                event.preventDefault();
            }

            function open_new_terminal(name) {
                var post_data = {
                    "name": name,
                    "startup_command": params["expanded_terminal_startup_command"]
                };
                if (params["expanded_terminal_switch_cwd"]) {
                    post_data["cwd"] = IPython.notebook_list.notebook_path;
                }
                var url = utils.url_path_join(base_url, "api/terminals");
                var settings = {
                    type: "POST",
                    dataType: "json",
                    data: JSON.stringify(post_data),
                    success: function(data, status, xhr) {
                        var name = data.name;
                        var w = window.open("#", IPython._target);
                        w.location = utils.url_path_join(
                            base_url, "terminals", utils.encode_uri_components(name)
                        );
                    },
                    error: function(jqXHR, status, error) {
                        if (params["expanded_terminal_custom_name"]) {
                            var err_msg = jqXHR.responseJSON.message;
                            var failmsg = "Failed to open a new terminal.";
                            var failbody = $("<div/>").text(failmsg).append(
                                $("<div/>").addClass("alert alert-danger").text(err_msg)
                            );
                            dialog.modal({
                                title: "Failed",
                                body: failbody,
                                buttons: {
                                    OK: {
                                        "class": "btn-primary"
                                    }
                                }
                            });
                        };
                        utils.log_ajax_error(jqXHR, status, error);
                    },
                };
                utils.ajax(url, settings);
            };

            if (!params["expanded_terminal_custom_name"]) {
                open_new_terminal();
            } else {
                input_terminal_name_dialog("Create", function() {
                    var input = $(".modal-dialog input");
                    open_new_terminal(input.val());
                });
            };
        };

        $("#new-terminal").unbind("click");
        var terminal_list = new TerminalList("#terminal_list", {
            base_url: utils.get_body_data("baseUrl")
        });
    }

    function expand_rename_terminal() {
        function rename_terminal(new_name) {
            var name = $("body").data("wsPath").replace(/terminals\/websocket\//i, "");
            name = decodeURIComponent(name);
            var post_data = {
                "new_name": new_name
            };
            var url = utils.url_path_join(base_url, "api/terminals", name);
            var settings = {
                type: "POST",
                dataType: "json",
                data: JSON.stringify(post_data),
                success: function(data, status, xhr) {
                    var name = data.name;
                    window.history.replaceState({}, "", utils.url_path_join(
                        base_url, "terminals", utils.encode_uri_components(name)
                    ));
                    $("span.term_name").text(name);
                    name = utils.encode_uri_components(name);
                    $("body").attr("data-ws-path", "terminals/websocket/" + name);
                    $("body").data("wsPath", "terminals/websocket/" + name);
                },
                error: function(jqXHR, status, error) {
                    var err_msg = jqXHR.responseJSON.message;
                    var failmsg = "Failed to open a new terminal.";
                    var failbody = $("<div/>").text(failmsg).append(
                        $("<div/>").addClass("alert alert-danger").text(err_msg)
                    );
                    dialog.modal({
                        title: "Failed",
                        body: failbody,
                        buttons: {
                            OK: {
                                "class": "btn-primary"
                            }
                        }
                    });
                    utils.log_ajax_error(jqXHR, status, error);
                },
            };
            utils.ajax(url, settings);
        }

        var cur_term_name = $("body").data("wsPath").replace(/terminals\/websocket\//i, "");
        cur_term_name = decodeURIComponent(cur_term_name);
        var term_name_span = $('<span id="terminal_name " class="filename term_name"></span>');
        var term_name_span = $("<span>").attr("id", "terminal_name");
        term_name_span.attr("class", "term_name filename");
        term_name_span.text(cur_term_name);
        $("#save_widget").append(term_name_span);
        term_name_span.unbind("click");
        term_name_span.click(function() {
            if (event) {
                event.preventDefault();
            }
            input_terminal_name_dialog("Rename", function() {
                var input = $(".modal-dialog input");
                rename_terminal(input.val());
            });
        });
    }

    function load_ipython_extension() {
        var url = utils.url_path_join(base_url, "terminal_extension");
        var settings = {
            type: "GET",
            dataType: "json",
            success: function(data, status, xhr) {
                config.load();
                expand_new_terminal();
                if ($("body").hasClass("terminal-app")) {
                    expand_rename_terminal();
                };
            },
            error: function(jqXHR, status, error) {
                utils.log_ajax_error(jqXHR, status, error);
                console.log(
                    "[Expanded Terminal]" +
                    "Server extension is unavaliable," +
                    "the frond-end extension would not load"
                );
            },
        };
        utils.ajax(url, settings);
    }

    return {
        load_ipython_extension: load_ipython_extension,
    };
});