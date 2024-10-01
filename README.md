# Package Comparator CLI

#### This tool allows you to compare binary packages between two branches (e.g., `sisyphus` and `p10`) in ALT Linux.

## Requirements

- Python 3.7+
- aiohttp==3.10.8
- click==8.1.7
- environs==11.0.0
- pytest==8.3.3
- pytest-mock==3.14.0
- pytest-mock==3.14.0
- rpm==0.2.0

#### Install dependencies using:

```bash
pip install -r requirements.txt
```

## Installation

#### Make the script executable and move it to a directory in your PATH:

```bash
chmod +x compare-packages
sudo cp compare-packages /usr/local/bin/
```

## Usage

#### Now you can run the tool as a standard CLI command to compare packages between two branches:
```bash
compare-packages --branch1=sisyphus --branch2=p10 --arch=x86_64
```

## Options
    --url: Base API URL (default: https://rdb.altlinux.org/api/export/branch_binary_packages).
    --branch1: First branch to compare (default: sisyphus).
    --branch2: Second branch to compare (default: p10).
    --arch: Package architecture (default: x86_64).
    --output: Output format (default: json).
    --output-file: Optional output to a file (if specified, the result is saved to a file).

### Example
```bash
compare-packages --branch1=sisyphus --branch2=p10 --arch=x86_64 --output=json --output-file=output.json
```

## Running Tests

### To run the tests:

```bash
pytest tests -v -s
```

#### Now you can test your utility and make sure it works like a regular command.
## Conclusion

#### Now the CLI utility works as a command in Linux. You can run it directly from the terminal and use all the options as specified in the instructions.