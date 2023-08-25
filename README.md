# CMDGPT

_CMDGPT_ is an open-source command-line tool that leverages Large Language Models (LLM) to execute various commands seamlessly. It's designed for developers, system administrators, or anyone who loves working from the command line. This project is currently compatible only with Mac and requires iTerm2.

## Features

- Automatic command-line parsing and execution using agent with MAPE loop
- Detailed logging for debugging or understanding the underlying processes
- iTerm2 integration for a smooth experience

## Requirements

- macOS
- Python 3.9
- iTerm2
- OpenAI API (GPT-3.5 or GPT-4)

## Configuration

Before running the project, you must configure the OpenAI API key. The system currently defaults to GPT-3.5, but you can also use GPT-4.

1. Locate the `config/key.yaml` file in the project directory.
2. Set the `OPENAI_API_KEY` value to your OpenAI API key.

Example:

```yaml
OPENAI_API_KEY: "your-openai-api-key-here"
```


## Installation

Before proceeding with the installation, ensure you have iTerm2 installed on your system.

First, clone the repository and navigate to the project directory.

### Using `requirements.txt`

You can install the required dependencies by running:

```bash
pip install -r requirements.txt
```

### Using `setup.py`

You can also install the package using one of the following commands:

For development:

```bash
python setup.py develop
```

For standard installation:

```bash
python setup.py install
```

## Usage

### Basic Command

You can run commands using the following syntax:

```bash
python run.py "your prompt"
```

### Example Prompts

```bash
python run.py "create a file called hello_world.txt"
```

or

```bash
python run.py "install docker in a Ubuntu 18.04 server with IP 192.168.0.42 with ssh username ubuntu, and run an nginx container at port 80"
```

### Logging

If you want to see the full internal logging of the template, etc., you can do:

```bash
python run.py "your prompt" --logger_level="DEBUG"
```

## Note

When running the commands, please ensure you have an iTerm2 window opened.

## Contributing

Contributions are welcome! Feel free to fork the repository and submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact

For any questions or issues, please [open an issue on GitHub](https://github.com/jyericlin/cmd_gpt/issues) or contact the maintainers directly.

Happy Commanding!
