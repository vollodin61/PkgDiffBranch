# Package Comparator CLI

#### This tool allows you to compare binary packages between two branches (e.g., `sisyphus` and `p10`) in ALT Linux.

## Installation
#### To install the utility, go to the project folder and enter the commands
```markdown
 git clone https://github.com/vollodin61/PkgDiffBranch.git
 cd PkgDiffBranch  
 python3 -m venv .venv
 source .venv/bin/activate
```
### Requirements

- Python 3.7+
- aiohttp==3.10.8
- click==8.1.7
- environs==11.0.0
- rpm==0.2.0  


- pytest==8.3.3
- pytest-asyncio==0.24.0
- pytest-mock==3.14.0

#### Install dependencies using:

```bash
pip install -r requirements.txt
```

#### To install the package and make it available as a command:
```bash
pip install .
```

## Usage
### Create a .env file
#### Create a .env file and add your URL to it, as shown in the example .env_temp file. You can create the file using the following command:
```bash
cp .env_temp .env
```
#### Then, open the .env file and replace the placeholder with your actual API URL.
```bash
nano .env  # Or use your preferred text editor
```
### Now you can run the tool as a standard CLI command to compare packages between two branches:
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