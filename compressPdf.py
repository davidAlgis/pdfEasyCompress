import argparse
import io
import os

import fitz  # PyMuPDF for JBIG2 decoding
import tqdm
from PIL import Image
from pypdf import PdfReader, PdfWriter


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def create_minimal_white_image():
    return Image.new("RGB", (1, 1), color="white")


def parse_page_numbers(pages_string):
    if not pages_string:
        return None
    pages = set()
    for part in pages_string.split(","):
        if "-" in part:
            start, end = map(int, part.split("-"))
            pages.update(range(start, end + 1))
        else:
            pages.add(int(part))
    return pages


def compress_image(image, quality=80, convert_png=True):
    if not isinstance(image, Image.Image):
        image = Image.open(io.BytesIO(image))

    img_format = image.format.lower() if image.format else "jpeg"
    if img_format == "jpeg" or (img_format == "png" and convert_png):
        if image.mode in ("RGBA", "LA") or (
            image.mode == "P" and "transparency" in image.info
        ):
            background = Image.new("RGBA", image.size, (255, 255, 255))
            image = Image.alpha_composite(
                background, image.convert("RGBA")
            ).convert("RGB")

        output = io.BytesIO()
        image.save(output, format="JPEG", quality=quality, optimize=True)

        if output.tell() < len(image.tobytes()):
            return Image.open(output)
    return image


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Reduce the size of images in a PDF file"
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="The PDF file to process",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="The name of the output PDF file",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=80,
        help="The quality of the JPEG images (default: 80)",
    )
    parser.add_argument(
        "-l",
        "--lossless",
        type=str2bool,
        nargs="?",
        const=True,
        default=False,
        help="Indicate if compression should be lossless (default is false)",
    )
    parser.add_argument(
        "-ri",
        "--removeImages",
        type=str2bool,
        nargs="?",
        const=True,
        default=False,
        help="Replace all images with a minimal white image (default: false)",
    )
    parser.add_argument(
        "-sp",
        "--selectPages",
        type=str,
        default="",
        help="Pages to keep, e.g., '1,3-5'",
    )
    parser.add_argument(
        "-cp",
        "--convertPNG",
        type=str2bool,
        nargs="?",
        const=True,
        default=True,
        help="Convert PNG images to JPEG (default: true)",
    )
    args = parser.parse_args()

    if args.output is None:
        args.output = os.path.splitext(args.input)[0] + "_compressed.pdf"

    pages_to_keep = parse_page_numbers(args.selectPages)
    try:
        reader = PdfReader(args.input)
    except FileNotFoundError:
        print(f"Error: File not found: {args.input}")
        exit(1)

    writer = PdfWriter()
    minimal_white_image = create_minimal_white_image()
    doc_fitz = fitz.open(args.input)

    print("Processing pages...")
    for i, page in enumerate(
        tqdm.tqdm(reader.pages, desc="Processing pages"), start=1
    ):
        if pages_to_keep and i not in pages_to_keep:
            continue
        writer_page = writer.add_page(page)
        fitz_page = doc_fitz.load_page(i - 1)
        fitz_images = fitz_page.get_images(full=True)

        # Safely fetch image wrappers
        try:
            imgs = list(writer_page.images)
        except NotImplementedError as e:
            print(f"⚠️ Skipping image-level processing on page {i}: {e}")
            imgs = []

        if args.removeImages:
            for img in imgs:
                img.replace(minimal_white_image)
        else:
            for img in imgs:
                if args.lossless:
                    continue
                try:
                    original_image = img.image
                except NotImplementedError:
                    # JBIG2 fallback via MuPDF
                    xref = img.objid
                    pix = next(
                        (
                            fitz_page.get_pixmap(xref=x)
                            for x, *_ in fitz_images
                            if x == xref
                        ),
                        None,
                    )
                    if not pix:
                        print(f"⚠️ JBIG2 XObject {xref} not found on page {i}")
                        continue
                    mode = "RGB" if pix.n >= 3 else "L"
                    original_image = Image.frombytes(
                        mode, (pix.width, pix.height), pix.samples
                    )
                    if pix.n == 4:
                        original_image = original_image.convert("RGB")

                compressed_image = compress_image(
                    original_image,
                    quality=args.quality,
                    convert_png=args.convertPNG,
                )
                if len(compressed_image.tobytes()) < len(
                    original_image.tobytes()
                ):
                    try:
                        img.replace(compressed_image)
                    except Exception as e:
                        print(f"⚠️ Failed to replace image on page {i}: {e}")

        if args.lossless:
            writer_page.compress_content_streams()

    temp_output = args.output + ".temp"
    try:
        with open(temp_output, "wb") as f:
            writer.write(f)
    except Exception as e:
        print(f"Error saving result: {e}")
        exit(1)

    in_size = os.path.getsize(args.input)
    out_size = os.path.getsize(temp_output)
    if out_size >= in_size:
        print(
            f"Warning: Compressed PDF is larger ({out_size} bytes) than original ({in_size} bytes). Keeping original."
        )
        os.remove(temp_output)
        final_path = args.input
    else:
        if os.path.exists(args.output):
            os.remove(args.output)
        os.rename(temp_output, args.output)
        final_path = args.output

    print(f"Done: saved {final_path}")
    print(
        f"Size: {os.path.getsize(final_path)} bytes (reduced {(in_size - os.path.getsize(final_path)) / in_size * 100:.2f}% )"
    )
