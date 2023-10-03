from PIL import Image
import argparse

symbols_dimension = 10

def print_to_console(arr):
    for y in range(len(arr)):
        for x in range(len(arr[y])):
            print(arr[y][x])
        print("endline")

def image_to_2d_array(image_path):
    img = Image.open(image_path)

    # Convert the image to RGB mode (just in case it's in another format)
    img = img.convert('RGB')

    width, height = img.size
    arr = [[0 for _ in range(width)] for _ in range(height)]

    for y in range(height):
        for x in range(width):
            r, g, b = img.getpixel((x, y))
            arr[y][x] = r

    return arr

def create_empty_image_to_size(arr):
    width = len(arr[0]) * symbols_dimension
    height = len(arr) * symbols_dimension
    image = Image.new("RGB", (width, height))
    return image

def fill_pattern(symbols_image, empty_image, pixels):
    for i, row in enumerate(pixels):
        for j, symbol_value in enumerate(row):
            if symbol_value == 255:
                symbol_value = 6

            symbol_x = (symbol_value % symbols_dimension) * symbols_dimension
            symbol_y = (symbol_value // symbols_dimension) * symbols_dimension
            
            symbol = symbols_image.crop((symbol_x, symbol_y, symbol_x + symbols_dimension, symbol_y + symbols_dimension))
            
            output_x = j * symbols_dimension
            output_y = i * symbols_dimension
            empty_image.paste(symbol, (output_x, output_y))
    return empty_image

def generate_cross_stitch_pattern(input_image_path, symbol_image_path, output_image_path):
    symbol_image = Image.open(symbol_image_path)

    pixel_values = image_to_2d_array(input_image_path)
    empty_image = create_empty_image_to_size(pixel_values)
    pattern_image = fill_pattern(symbol_image, empty_image, pixel_values)
    
    pattern_image.save(output_image_path)
    print("Saved image to " + output_image_path)

def main():
    parser = argparse.ArgumentParser(description="Generate cross-stitch pattern from image.")
    parser.add_argument("input_image_path", help="Path to the input image.")
    parser.add_argument("symbol_image_path", help="Path to the symbol image.")
    parser.add_argument("output_image_path", help="Path to save the generated pattern image.")

    args = parser.parse_args()

    generate_cross_stitch_pattern(args.input_image_path, args.symbol_image_path, args.output_image_path)

if __name__ == "__main__":
    main()
