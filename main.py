from PIL import Image, ImageDraw, ImageFont
import numpy as np
from sklearn.cluster import KMeans
import argparse

# python main.py "symbol_path" "output_path" "input_path"
# python main.py "C:\Users\Zroix\Documents\stitch-pix\Examples\Satoshi-Variable.ttf" "C:\Users\Zroix\Documents\stitch-pix\Examples\crossstitch_symbols.png" "C:\Users\Zroix\Documents\stitch-pix\Examples" "C:\Users\Zroix\Documents\stitch-pix\Examples\onlyhead_final.png"

symbols_dimension = 10
total_colors = 5
font_size = 12
font_color = (0, 0, 0, 255)

def kmeans_color_quantization(reference_image):
    pixel_list = []
    width, height = reference_image.size
    for y in range(height):
        for x in range(width):
            pixel = reference_image.getpixel((x, y))
            if pixel[3] != 0:
                pixel_list.append(pixel[:3])

    pixel_array = np.array(pixel_list)
    
    # Apply KMeans clustering
    kmeans = KMeans(n_clusters=total_colors, random_state=42)
    kmeans.fit(pixel_array)
    cluster_centers = kmeans.cluster_centers_
    labels = kmeans.labels_
    cluster_centers = np.rint(cluster_centers).astype(int)
    
    # Map the clustered colors back to the original format
    new_pixels = []
    index = 0
    for y in range(height):
        new_row = []
        for x in range(width):
            pixel = reference_image.getpixel((x, y))
            if pixel[3] == 0:
                new_row.append((0, 0, 0, 0))
            else:
                r, g, b = tuple(cluster_centers[labels[index]])
                new_row.append((r, g, b, 255))
                index += 1
        new_pixels.append(new_row)

    return new_pixels

def create_empty_image_to_size(reference_image):
    width, height = reference_image.size
    image = Image.new("RGBA", (width * symbols_dimension, height * symbols_dimension), "white")
    return image

def fill_pattern(reference_image, symbols_array, empty_image, pixel_dictionary):
    width, height = reference_image.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = reference_image.getpixel((x, y))
            output_x = x * symbols_dimension
            output_y = y * symbols_dimension
            if a != 0:
                empty_image.paste(symbols_array[pixel_dictionary[(r, g, b, 255)]], (output_x, output_y))
    return empty_image

def fill_reference_image(pixels):
    image = Image.new("RGBA", (len(pixels[0]), len(pixels)), "white")
    for y, row in enumerate(pixels):
        for x, pixel in enumerate(row):
            if pixel[3] == 0:
                image.putpixel((x, y), (0, 0, 0, 0))
            else:
                r, g, b, a = pixel
                image.putpixel((x, y), (r, g, b, 255))
    width, height = image.size
    return image

def get_unique_pixels(reference_image):
    unique_pixels = set()
    width, height = reference_image.size
    for y in range(height):
        for x in range(width):
            pixel = reference_image.getpixel((x, y))
            if pixel[3] != 0:
                unique_pixels.add(pixel)
    
    return sorted(unique_pixels)

def make_pixel_dictionary(unique_pixels):
    pixel_dictionary = {}
    for i in range(len(unique_pixels)):
        pixel_dictionary[unique_pixels[i]] = i
    return pixel_dictionary

def make_symbol_array(symbols_image):
    symbols_array = []
    width, height = symbols_image.size
    for x in range(int(width / symbols_dimension)):
        for y in range(int(height / symbols_dimension)):
            symbol_x = x * symbols_dimension
            symbol_y = y * symbols_dimension
            symbol = symbols_image.crop((symbol_x, symbol_y, symbol_x + symbols_dimension, symbol_y + symbols_dimension))
            symbols_array.append(symbol)
    return symbols_array

def create_symbol_color_reference(unique_pixels, pixel_dictionary, symbols_array, font_path):
    image = Image.new("RGB", (symbols_dimension*5 + font_size * 5, ((symbols_dimension+5)*len(unique_pixels)) + 10), "white")
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        font = ImageFont.load_default()

    for i in range(len(unique_pixels)):
        row_y = 5 + (i * (symbols_dimension + 5))

        pixel = unique_pixels[i]
        index = pixel_dictionary[pixel]
        symbol = symbols_array[index]
        image.paste(symbol, (5, row_y))
        draw.rectangle([10 + symbols_dimension, row_y, 10 + (symbols_dimension*2), row_y + symbols_dimension], fill=unique_pixels[i])
        draw.text([10 + symbols_dimension + 20, row_y], "#{:02X}{:02X}{:02X}".format(pixel[0], pixel[1], pixel[2]), font=font, fill=font_color)
    return image

def generate_cross_stitch_pattern(input_image_path, symbols_image_path, output_image_path, font_path):
    symbols_image = Image.open(symbols_image_path)
    symbols_array = make_symbol_array(symbols_image)

    reference_image = Image.open(input_image_path)
    pixel_array_consolidated = kmeans_color_quantization(reference_image)

    unique_pixels_array_preconsolidated = get_unique_pixels(reference_image)

    reference_image_consolidated = fill_reference_image(pixel_array_consolidated)
    ref_path = output_image_path+"\ef_.png"
    reference_image_consolidated.save(ref_path)
    print("Saved consolidated reference image to " + ref_path)

    unique_pixels_array = get_unique_pixels(reference_image_consolidated)

    print("Reduced from " + str(len(unique_pixels_array_preconsolidated)) + " to " + str(len(unique_pixels_array)) + " colors")

    if len(symbols_array) < len(unique_pixels_array):
        print("Not enough symbols (" + str(len(symbols_array)) + ") for amount of unique pixels (" + str(len(unique_pixels_array)) + ")")
        return

    pixel_dictionary = make_pixel_dictionary(unique_pixels_array)
    color_reference = create_symbol_color_reference(unique_pixels_array, pixel_dictionary, symbols_array, font_path)
    color_reference_path = output_image_path+"\color_reference.png"
    color_reference.save(color_reference_path)
    print("Saved color reference to " + color_reference_path)

    empty_image = create_empty_image_to_size(reference_image_consolidated)
    pattern_image = fill_pattern(reference_image_consolidated, symbols_array, empty_image, pixel_dictionary)
    pattern_path = output_image_path+"\pattern.png"
    pattern_image.save(pattern_path)
    print("Saved image to " + pattern_path)

def main():
    parser = argparse.ArgumentParser(description="Generate cross-stitch pattern from image.")
    parser.add_argument("font_path", help="Path to the font file.")
    parser.add_argument("symbols_image_path", help="Path to the symbol image.")
    parser.add_argument("output_image_path", help="Path to map to save generated pattern and color reference.")
    parser.add_argument("input_image_path", help="Path to the input image.")

    args = parser.parse_args()

    generate_cross_stitch_pattern(args.input_image_path, args.symbols_image_path, args.output_image_path, args.font_path)

if __name__ == "__main__":
    main()
