import click

from lexer import Lexer


@click.command()
@click.option('--file', '-f', help='Name of the file')
def main(file):
    lexer = Lexer()
    lexer.run(file)


if __name__ == '__main__':
    main()
