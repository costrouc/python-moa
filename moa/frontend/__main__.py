from .moa import MOAParser


if __name__ == "__main__":
    parser = MOAParser()

    print('MOA Calculator')
    while True:
        text = input('>>> ')
        if text in {'q', 'quit'}: break
        print(parser.parse(text))
