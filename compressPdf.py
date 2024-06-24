import argparse
from pypdf import PdfReader, PdfWriter
from PIL import Image
import io
import tqdm
import os

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def create_minimal_white_image():
    # Create a 1x1 white image
    return Image.new('RGB', (1, 1), color='white')

# Create the parser
parser = argparse.ArgumentParser(
    description="Reduce the size of images in a PDF file")

# Add the arguments
parser.add_argument('-i', '--input', type=str, help='The PDF file to process')
parser.add_argument('-o', '--output', type=str, default=None, help='The name of the output PDF file')
parser.add_argument('-q', '--quality', type=int, default=80, help='The quality of the images (default: 80)')
parser.add_argument("-l", "--lossless", type=str2bool, nargs='?', const=True, default=True,
                    help="Indicate if compression should be lossless. If true the quality parameters for images will not be applied (default is true)")
parser.add_argument("-ri", "--removeImages", type=str2bool, nargs='?', const=True, default=False,
                    help="Replace all images with a minimal white image (default: false)")

# Parse the arguments
args = parser.parse_args()

# If no output file is specified, use the same name as the input file
if args.output is None:
    args.output = os.path.splitext(args.input)[0] + "_compressed.pdf"


if(args.lossless):
    print("Performs a lossless compression...")
    try:
        writer = PdfWriter(clone_from=args.input)
    except FileNotFoundError:
        print(f"Error: The file '{args.input}' was not found.")
        exit(1)
    for page in writer.pages:
        try:
            page.compress_content_streams()  # This is CPU intensive!
        except Exception as e:
            print(f"Error: unable to compress content streams. {e}")
            exit(1)
else:
    print("Performs a lossy compression...")

    try:
        reader = PdfReader(args.input)
    except FileNotFoundError:
        print(f"Error: The file '{args.input}' was not found.")
        exit(1)

    writer = PdfWriter()

    # Create a minimal white image
    minimal_white_image = create_minimal_white_image()

    # Process pages
    print("Processing pages...")
    for page in tqdm.tqdm(reader.pages, desc="Processing pages"):
        # Add the page to the writer
        writer_page = writer.add_page(page)
        
        if args.removeImages:
            for img in writer_page.images:
                img.replace(minimal_white_image)
        elif not args.lossless:
            for img in writer_page.images:
                img.replace(img.image, quality=args.quality)
        
        if args.lossless:
            writer_page.compress_content_streams()

# Save the result
try:
    with open(args.output, "wb") as f:
        writer.write(f)
except Exception as e:
    print(f"Error: Failed to save the result. {e}")
    exit(1)

print(f"Done. The result is saved at {args.output}")

# Check the size of the compressed file and calculate the percentage of size reduction
input_size = os.path.getsize(args.input) / (1024 * 1024)
output_size = os.path.getsize(args.output) / (1024 * 1024)
size_reduction = (input_size - output_size) / input_size * 100
print(f"The output file size is {output_size:.2f} MiB which gave us a size reduction of {size_reduction:.2f}%.")
