from PIL import Image, ImageDraw
import argparse

symbols_dimension = 10
consolidation_threshold = 5

def print_to_console(arr):
    for y in range(len(arr)):
        for x in range(len(arr[y])):
            print(arr[y][x])
        print("endline")

def image_to_2d_array(image_path):
    img = Image.open(image_path)

    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    width, height = img.size
    arr = [[0 for _ in range(width)] for _ in range(height)]

    for y in range(height):
        for x in range(width):
            r, g, b, a = img.getpixel((x, y))
            if a == 0:
                arr[y][x] = "0"
            else:
                arr[y][x] = f"{r:03}{g:03}{b:03}"

    return arr

def create_empty_image_to_size(arr):
    width = len(arr[0]) * symbols_dimension
    height = len(arr) * symbols_dimension
    image = Image.new("RGB", (width, height), "white")
    return image

def fill_pattern(symbols_array, empty_image, pixels, pixel_dictionary):
    for i, row in enumerate(pixels):
        for j, pixel_value in enumerate(row):
            output_x = j * symbols_dimension
            output_y = i * symbols_dimension
            if pixel_value != "0":
                empty_image.paste(symbols_array[pixel_dictionary[pixel_value]], (output_x, output_y))
    return empty_image

def fill_reference_image(pixels, unique_pixels):
    image = Image.new("RGB", (len(pixels[0]), len(pixels)), "white")
    draw = ImageDraw.Draw(image)
    for i, row in enumerate(pixels):
        for j, pixel_value in enumerate(row):
            if pixel_value != "0":
                rgb_string = pixel_value
                r = int(rgb_string[:3])
                g = int(rgb_string[3:6])
                b = int(rgb_string[6:])
                draw.rectangle([j, i, j, i], fill=(r,g,b))
    return image

def consolidate_pixels(pixel_values):
    pixel_count = {}
    for row in pixel_values:
        for column in row:
            if column in pixel_count:
                pixel_count[column] += 1
                continue
            pixel_count[column] = 1

    need_consolidate = True
    while need_consolidate:
        need_consolidate = False
        for x, row in enumerate(pixel_values):
            for y, column in enumerate(row):
                if pixel_count[column] <= consolidation_threshold:
                    if x > 0 and pixel_count[pixel_values[x-1][y]] > consolidation_threshold:
                        pixel_values[x][y] = pixel_values[x-1][y]
                    elif x < 1-len(pixel_values[0]) and pixel_count[pixel_values[x+1][y]] > consolidation_threshold:
                        pixel_values[x][y] = pixel_values[x+1][y]
                    elif y > 0 and pixel_count[pixel_values[x][y-1]] > consolidation_threshold:
                        pixel_values[x][y] = pixel_values[x][y-1]
                    elif y < 1-len(pixel_values) and pixel_count[pixel_values[x][y+1]] > consolidation_threshold:
                        pixel_values[x][y] = pixel_values[x][y+1]
                    else:
                        need_consolidate = True
    return pixel_values

def get_unique_pixels(pixel_values):
    unique_pixels = []
    for row in pixel_values:
        for column in row:
            if column == "0" or column in unique_pixels:
                continue
            unique_pixels.append(column)
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

def create_symbol_color_reference(unique_pixels, pixel_dictionary, symbols_array):
    image = Image.new("RGB", (symbols_dimension*10, (symbols_dimension*len(unique_pixels)) + 10), "white")
    draw = ImageDraw.Draw(image)
    for i in range(len(unique_pixels)):
        row_y = 5 + (i * symbols_dimension)

        index = pixel_dictionary[unique_pixels[i]]
        symbol = symbols_array[index]
        image.paste(symbol, (5, row_y))

        rgb_string = unique_pixels[i]
        r = int(rgb_string[:3])
        g = int(rgb_string[3:6])
        b = int(rgb_string[6:])
        draw.rectangle([10 + symbols_dimension, row_y, 10 + (symbols_dimension*2), row_y + symbols_dimension], fill=(r,g,b))
    return image

def generate_cross_stitch_pattern(input_image_path, symbols_image_path, output_image_path):
    symbols_image = Image.open(symbols_image_path)
    symbols_array = make_symbol_array(symbols_image)

    pixel_values = image_to_2d_array(input_image_path)

    pixel_values = consolidate_pixels(pixel_values)

    unique_pixels = get_unique_pixels(pixel_values)

    print("Unique pixel colors: " + str(len(unique_pixels)))

    if len(symbols_array) < len(unique_pixels):
        print("Not enough symbols (" + str(len(symbols_array)) + ") for unique pixels (" + str(len(unique_pixels)) + ")")
        return

    pixel_dictionary = make_pixel_dictionary(unique_pixels)
    color_reference = create_symbol_color_reference(unique_pixels, pixel_dictionary, symbols_array)
    color_reference_path = output_image_path+"\color_reference.png"
    color_reference.save(color_reference_path)
    print("Saved color reference to " + color_reference_path)

    empty_image = create_empty_image_to_size(pixel_values)
    pattern_image = fill_pattern(symbols_array, empty_image, pixel_values, pixel_dictionary)
    
    pattern_path = output_image_path+"\pattern.png"
    pattern_image.save(pattern_path)
    print("Saved image to " + pattern_path)

    reference_image_consolidated = fill_reference_image(pixel_values, unique_pixels)
    ref_path = output_image_path+"\ef_.png"
    reference_image_consolidated.save(ref_path)
    print("Saved consolidated reference image to " + ref_path)

def main():
    parser = argparse.ArgumentParser(description="Generate cross-stitch pattern from image.")
    parser.add_argument("input_image_path", help="Path to the input image.")
    parser.add_argument("symbols_image_path", help="Path to the symbol image.")
    parser.add_argument("output_image_path", help="Path to map to save generated pattern and color reference.")

    args = parser.parse_args()

    generate_cross_stitch_pattern(args.input_image_path, args.symbols_image_path, args.output_image_path)

if __name__ == "__main__":
    main()
