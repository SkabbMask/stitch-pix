from PIL import Image, ImageDraw, ImageFont
import numpy as np
from sklearn.cluster import KMeans
import os

marginWidth = 90

def read_config_file(file_path):
    config = {}
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
    return config

def kmeans_color_quantization(reference_image, total_colors):
    pixel_list = []
    width, height = reference_image.size
    for y in range(height):
        for x in range(width):
            pixel = reference_image.getpixel((x, y))
            if len(pixel) >= 4 and pixel[3] == 0:
                continue
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
            if len(pixel) >= 4 and pixel[3] == 0:
                new_row.append((0, 0, 0, 0))
            else:
                r, g, b = tuple(cluster_centers[labels[index]])
                new_row.append((r, g, b, 255))
                index += 1
        new_pixels.append(new_row)

    return new_pixels

def create_empty_image_to_size(reference_image, symbols_dimension):
    width, height = reference_image.size
    image = Image.new("RGBA", ((width * symbols_dimension) + marginWidth*2, (height * symbols_dimension) + marginWidth*2), "white")
    return image

def fill_with_squares(empty_image, config):

    _font_s = int(config['font_size'])
    _dim = int(config['symbols_dimension'])

    try:
        font = ImageFont.truetype(config['font_path'], _font_s)
    except IOError:
        font = ImageFont.load_default()

    width, height = empty_image.size
    squaresWidth = int(((width - (marginWidth*2)) / _dim) + 1)
    squaresHeight = int(((height - (marginWidth*2)) / _dim) + 1)
    draw = ImageDraw.Draw(empty_image)
    text_height = _font_s
    for y in range(squaresHeight):
        lineWidth = 1
        y_pos = (y * _dim) + marginWidth
        if y % 10 == 0:
            bbox = draw.textbbox((0,0), str(y), font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            draw.text([marginWidth - text_width - 4, y_pos], str(y), font=font, fill=(0, 0, 0, 255))
            lineWidth = 2
            y_pos -= 1
        draw.rectangle([marginWidth, y_pos, width - marginWidth, y_pos + lineWidth], fill=(0, 0, 0, 255))

    for x in range(squaresWidth):
        lineWidth = 1
        x_pos = (x * _dim) + marginWidth
        if x % 10 == 0:
            draw.text([x_pos, marginWidth - (text_height * 2)], str(x), font=font, fill=(0, 0, 0, 255))
            lineWidth = 2
            x_pos -= 1
        draw.rectangle([x_pos, marginWidth, x_pos + lineWidth, height - marginWidth], fill=(0, 0, 0, 255))
    return empty_image

def fill_pattern(reference_image, symbols_array, empty_image, pixel_dictionary, symbols_dimension):
    width, height = reference_image.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = reference_image.getpixel((x, y))
            output_x = (x * symbols_dimension) + marginWidth
            output_y = (y * symbols_dimension) + marginWidth
            if a != 0:
                empty_image.paste(symbols_array[pixel_dictionary[(r, g, b, 255)]], (output_x, output_y))
    return empty_image

def fill_reference_image(pixels):
    image = Image.new("RGBA", (len(pixels[0]), len(pixels)), "white")
    for y, row in enumerate(pixels):
        for x, pixel in enumerate(row):
            if len(pixel) >= 4 and pixel[3] == 0:
                image.putpixel((x, y), (0, 0, 0, 0))
            elif len(pixel) < 4 or pixel[3] != 0:
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
            if len(pixel) >= 4 and pixel[3] == 0:
                continue
            unique_pixels.add(pixel)
    
    return sorted(unique_pixels)

def make_pixel_dictionary(unique_pixels):
    pixel_dictionary = {}
    for i in range(len(unique_pixels)):
        pixel_dictionary[unique_pixels[i]] = i
    return pixel_dictionary

def make_symbol_array(symbols_image, symbols_dimension):
    symbols_array = []
    width, height = symbols_image.size
    for x in range(int(width / symbols_dimension)):
        for y in range(int(height / symbols_dimension)):
            symbol_x = x * symbols_dimension
            symbol_y = y * symbols_dimension
            symbol = symbols_image.crop((symbol_x, symbol_y, symbol_x + symbols_dimension, symbol_y + symbols_dimension))
            symbols_array.append(symbol)
    return symbols_array

def make_color_count(pixels):
    count_dict = {}
    for y, row in enumerate(pixels):
        for x, pixel in enumerate(row):
            if len(pixel) >= 4 and pixel[3] == 0:
                continue
            if pixel in count_dict:
                count_dict[pixel] += 1
            else:
                count_dict[pixel] = 1
    return count_dict

def create_symbol_color_reference(unique_pixels, pixel_dictionary, symbols_array, pixel_count, config):
    # 100 x [symbol] [color] HEXCOLOR
    
    _font_s = int(config['font_size'])
    _dim = int(config['symbols_dimension'])

    max_key = max(pixel_count, key=pixel_count.get)
    max_count = pixel_count[max_key]
    count_x = 1
    sym_x = count_x + (len(str(max_count) + " x") * _font_s) + 2
    col_x = sym_x + _dim + 2
    hex_x = col_x + _dim + 2
    end_x = hex_x + (7 * _font_s) + 2

    height = ((_dim+5)*len(unique_pixels)) + _dim
    image = Image.new("RGB", (end_x, height), "white")
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype(config['font_path'], _font_s)
    except IOError:
        font = ImageFont.load_default()

    total_count = 0
    for i in range(len(unique_pixels)):
        row_y = 5 + (i * (_dim + 5))

        pixel = unique_pixels[i]
        index = pixel_dictionary[pixel]
        symbol = symbols_array[index]
        draw.text([count_x, row_y], str(pixel_count[pixel]) + "x", font=font, fill=(0, 0, 0, 255))
        image.paste(symbol, (sym_x, row_y))
        draw.rectangle([col_x, row_y, col_x + _dim, row_y + _dim], fill=unique_pixels[i])
        draw.text([hex_x, row_y], "#{:02X}{:02X}{:02X}".format(pixel[0], pixel[1], pixel[2]), font=font, fill=(0, 0, 0, 255))
        total_count += pixel_count[pixel]
    draw.text([count_x, height - (_font_s*2)], "Total: " + str(total_count), font=font, fill=(0, 0, 0, 255))
    return image

def generate_cross_stitch_pattern():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(script_dir, 'config.txt')
    config = read_config_file(config_file_path)

    symbols_image = Image.open(config['symbols_image_path'])
    symbols_array = make_symbol_array(symbols_image, int(config['symbols_dimension']))

    reference_image = Image.open(config['image_path'])
    pixel_array_consolidated = kmeans_color_quantization(reference_image, int(config['total_colors']))

    reference_image_consolidated = fill_reference_image(pixel_array_consolidated)
    ref_path = config['output_path'] + "\ef_.png"
    reference_image_consolidated.save(ref_path)
    print("Saved consolidated reference image to " + ref_path)

    unique_pixels_array = get_unique_pixels(reference_image_consolidated)

    if len(symbols_array) < len(unique_pixels_array):
        print("Not enough symbols (" + str(len(symbols_array)) + ") for amount of unique pixels (" + str(len(unique_pixels_array)) + ")")
        return

    pixel_count = make_color_count(pixel_array_consolidated)
    pixel_dictionary = make_pixel_dictionary(unique_pixels_array)
    color_reference = create_symbol_color_reference(unique_pixels_array, pixel_dictionary, symbols_array, pixel_count, config)
    color_reference_path = config['output_path'] + "\color_reference.png"
    color_reference.save(color_reference_path)
    print("Saved color reference to " + color_reference_path)

    empty_image = create_empty_image_to_size(reference_image_consolidated, int(config['symbols_dimension']))
    pattern_image = fill_pattern(reference_image_consolidated, symbols_array, empty_image, pixel_dictionary, int(config['symbols_dimension']))
    image = fill_with_squares(pattern_image, config)
    pattern_path = config['output_path'] + "\pattern.png"
    image.save(pattern_path)
    print("Saved image to " + pattern_path)

def main():
    generate_cross_stitch_pattern()

if __name__ == "__main__":
    main()
