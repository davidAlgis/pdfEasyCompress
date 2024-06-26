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
python compressPdf.py -i input.pdf -l False -q 50 
```

For a lossy compression that gives the best compromise between the ratio quality/size we advise to use this command :

```
python compressPdf.py -i input.pdf -l False -q 80 -cp True 
```

For a lossy compression to have the best size we advise to remove completely the images with this commands :

```
python compressPdf.py -i input.pdf -l False -ri True
```

## Options

   - `-i`, `--input` <file>: Specify the PDF file to compress.
   - `-o`, `--output` <file>: Specify the name of the output PDF file. If not specified, the output file will have the same name as the input file, but with `_compressed` added to the name and the same file extension.
   - `-l`, `--lossless` <True/False>: Indicate whether the script should apply lossless or lossy compression. If true the quality and remove images arguments won't be applied. Defaults to `True`.
   - `-q`, `--quality` <percent>: The quality of the images (default: `80`). 
   - `-ri`, `--removeImages` <True/False>: Replace all images with a minimal sized image (default: false) (default: `False`). If true the quality arguments won't be applied.
   - `-h`, `--help`: Display help information showing all command-line options.
   - `-sp`, `--selectPages` <pages>: Comma-separated list of page numbers or ranges to keep (e.g., '1,3-5,7'). If not specified, all pages are kept.
   - `-cp`, `--convertPNG` <True/False>: Convert PNG images to JPEG for further compression (default: True).


## Note

This script uses the PyPDF library to read and write PDF files, and the Pillow (PIL) library for image processing. It can perform the following operations:

- Lossless compression of PDF content streams
- Lossy compression of JPEG images
- Conversion of PNG images to JPEG (optional)
- Removal of specific pages
- Remove all the images

When converting PNGs to JPEGs, the script handles transparency by blending the image with a white background. This can result in __significant file size reduction__ but may affect the quality of images with text or sharp edges.

Remember to adjust the compression settings based on your specific needs and the nature of the images in your PDF files.