

# Jupyter Expanded Terminal

Make the terminal more convenient to use.


## Install

```
pip install git+git://github.com/jinzhen-lin/jupyter_expanded_terminal.git
jupyter nbextension install --py jupyter_expanded_terminal --sys-prefix
jupyter nbextension enable --py jupyter_expanded_terminal --sys-prefix
jupyter serverextension enable --py jupyter_expanded_terminal --sys-prefix
```


## Features

- custom terminal name: you can input custom name of new terminal
- rename terminal name: the terminal name would be show on the top the terminal page, you can click the terminal name to rename the terminal name
- auto switch working directory: the working directory of new terminal would switch to the current tree path automatically
- custom startup command: you can set commands to run in the new terminal after startup

