# PDF Compressor

This Python script allows you to compress PDF files by performing lossless or lossy compression on images.

## Installation

Before running the script, you need to install the required Python libraries. You can install them using the provided `requirements.txt` file.

```
pip install -r requirements.txt
```

## Usage

To use this script, run it from the command line and specify at least the input file. For example, this command line compress the file `input.pdf` into the file `input_compressed.pdf` with a lossy compression by reducing the quality of images of 50 percents :

```
python compressor.py -i input.pdf -l False -q 50 
```


## Options

   - `-i`, `--input` <file>: Specify the PDF file to compress.
   - `-o`, `--output` <file>: Specify the name of the output PDF file. If not specified, the output file will have the same name as the input file, but with `_compressed` added to the name and the same file extension.
   - `l`, `--lossless` <True/False>: Indicate whether the script should apply lossless or lossy compression. If true the quality arguments won't be applied. Defaults to `True`.
   - `q`, `--quality` <percent>: The quality of the images (default: `80`).
   - `-h`, `--help`: Display help information showing all command-line options.

## Note

This script uses the [PyPDF2](https://pypdf.readthedocs.io/en/stable/user/file-size.html) library to compress PDF files.