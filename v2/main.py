from PIL import Image, ImageDraw, ImageFont
import json
import os
import argparse
import sys


class Create_content_page():

    def __init__(self) -> None:
        args = self.create_console_args()
        self.read_content_json(args.input)
        self.read_settings_json(args.settings)
        img = self.draw_page()
        # img.show()
        img.save(f"{args.output}/{args.name}")
        print("Done!")

    def create_console_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", '--input', required=True,
                            help="Path to json with info", type=str)
        parser.add_argument("-o", '--output', required=True,
                            help="Path where to save the image", type=str)
        parser.add_argument("-n", '--name', required=True,
                            help="Name of img", type=str)
        parser.add_argument("-s", '--settings', required=True,
                            help="Path to json with settings", type=str)
        args = parser.parse_args()
        self.check_console_args(args)
        return args

    def check_console_args(self, args):
        if not os.path.exists(args.input and not args.input.endswith("json")):
            print("Error: The json file does not exist on this path")
            quit()

        if not os.path.exists(args.settings and not args.settings.endswith("json")):
            print("Error: The json file does not exist on this path")
            quit()

        if not os.path.exists(args.output):
            print(os.path.exists(args.output))
            print("Error: The directory does not exist on this path")
            quit()

        if not os.path.isdir(args.output):
            print("Error: This is not a directory")
            quit()

    def read_content_json(self, path):
        with open(path, "r", encoding="utf-8") as f:
            content: dict = json.loads(f.read())

        self.title: str = content["title"]
        self.chapters: tuple = content["chapters"]

    def read_settings_json(self, path):
        with open(path, "r", encoding="utf-8") as f:
            settings: dict = json.loads(f.read())
        self.page_resolution: tuple = settings["page"]["resolution"]
        self.page_right_margin: int = settings["page"]["right_margin"]
        self.page_left_margin: int = settings["page"]["left_margin"]
        self.page_top_margin: int = settings["page"]["top_margin"]
        self.page_bottom_margin: int = settings["page"]["bottom_margin"]
        self.page_color: str = settings["page"]["color"]

        self.title_font: str = settings["title"]["font"]
        self.title_font_size: int = settings["title"]["font_size"]
        self.title_min_font_size: str = settings["title"]["min_font_size"]
        self.title_font_color: str = settings["title"]["font_color"]

        self.subtitle_text: str = settings["subtitle"]["text"]
        self.subtitle_font: str = settings["subtitle"]["font"]
        self.subtitle_font_size: int = settings["subtitle"]["font_size"]
        self.subtitle_min_font_size: int = settings["subtitle"]["min_font_size"]
        self.subtitle_font_color: str = settings["subtitle"]["font_color"]

        self.content_style_align: str = settings["content"]["style"]["align"]
        self.content_style_use_two_columns: bool = settings["content"]["style"]["use_two_columns"]
        self.content_style_mirror_columns: bool = settings["content"]["style"]["mirror_columns"]

        self.content_author_font: str = settings["content"]["author"]["font"]
        self.content_author_font_size: int = settings["content"]["author"]["font_size"]
        self.content_author_min_font_size: int = settings["content"]["author"]["min_font_size"]
        self.content_author_font_color: str = settings["content"]["author"]["font_color"]

        self.content_title_font: str = settings["content"]["title"]["font"]
        self.content_title_font_size: int = settings["content"]["title"]["font_size"]
        self.content_title_min_font_size: int = settings["content"]["title"]["min_font_size"]
        self.content_title_font_color: str = settings["content"]["title"]["font_color"]

        self.content_page_number_font: str = settings["content"]["page_number"]["font"]
        self.content_page_number_font_size: int = settings["content"]["page_number"]["font_size"]
        self.content_page_number_font_color: str = settings["content"]["page_number"]["font_color"]

        self.space_title_to_subtitle: int = settings["space"]["title_to_subtitle"]
        self.space_sibtitle_to_content: int = settings["space"]["sibtitle_to_content"]
        self.space_author_to_title: int = settings["space"]["author_to_title"]
        self.space_title_to_page_number: int = settings["space"]["title_to_page_number"]
        self.space_title_to_autor: int = settings["space"]["title_to_autor"]
        self.space_between_columns: int = settings["space"]["between_columns"]

    def draw_page(self) -> Image.Image:
        if self.page_resolution[0] == "auto" and self.page_resolution[1] == "auto":
            render_resolution = [
                self.dynamic_width_calc(), self.dynamic_height_calc()]
        elif self.page_resolution[0] == "auto":
            render_resolution = [
                self.dynamic_width_calc(), self.page_resolution[1]]
        elif self.page_resolution[1] == "auto":
            render_resolution = [self.page_resolution[0],
                                 self.dynamic_height_calc()]
        else:
            render_resolution = self.page_resolution

        self.img = Image.new("RGB", render_resolution, color=self.page_color)
        self.draw_text = ImageDraw.Draw(self.img)

        if self.content_style_use_two_columns and self.is_enough_space_for_two_columns(render_resolution):
            self.draw_titles(render_resolution)
            self.draw_content_two_columns(render_resolution)

        else:
            self.draw_titles(render_resolution)
            self.draw_content(render_resolution)

        return self.img

    def dynamic_width_calc(self) -> int:
        content_block_width: int = self.space_title_to_page_number
        longest_title: int = self.get_longest_line(ImageFont.truetype(
            self.content_title_font, self.content_title_font_size), "title")
        longest_page_number: int = self.get_longest_line(ImageFont.truetype(
            self.content_page_number_font, self.content_page_number_font_size), "pages")
        if self.content_style_use_two_columns:
            content_block_width += int((longest_title + longest_page_number)
                                       * 2 + self.space_between_columns)
        else:
            content_block_width += longest_title + longest_page_number
        title_width = self.get_text_size(self.title, ImageFont.truetype(
            self.title_font, self.title_font_size))[0]
        subtitle_width = self.get_text_size(self.subtitle_text, ImageFont.truetype(
            self.subtitle_font, self.subtitle_font_size))[0]
        return max([content_block_width, title_width, subtitle_width]) + self.page_left_margin + self.page_right_margin

    def dynamic_height_calc(self) -> int:
        page_height: int = self.page_top_margin + self.page_bottom_margin + \
            self.space_title_to_subtitle + self.space_sibtitle_to_content

        title_height = self.get_text_size(self.title, ImageFont.truetype(
            self.title_font, self.title_font_size))[1]
        subtitle_height = self.get_text_size(self.subtitle_text, ImageFont.truetype(
            self.subtitle_font, self.subtitle_font_size))[1]
        page_height += title_height + subtitle_height

        highest_author = self.get_highest_line(ImageFont.truetype(
            self.content_author_font, self.content_author_font_size), "author")
        highest_title = self.get_highest_line(ImageFont.truetype(
            self.content_title_font, self.content_title_font_size), "title")

        if self.content_style_use_two_columns and self.is_enough_space_for_two_columns([self.dynamic_width_calc(), 0]):
            page_height += highest_author + highest_title + (self.space_author_to_title +
                                                             self.space_title_to_autor) * int(len(self.chapters)/2) - self.space_title_to_autor
        else:
            page_height += highest_author + highest_title + (self.space_author_to_title +
                                                             self.space_title_to_autor) * len(self.chapters) - self.space_title_to_autor
        return page_height

    def is_enough_space_for_two_columns(self, render_resolution: int) -> bool:
        dead_space: int = self.page_left_margin + \
            self.page_right_margin + self.space_between_columns
        space_for_column = int((render_resolution[0] - dead_space) / 2)

        longest_title: int = self.get_longest_line(ImageFont.truetype(
            self.content_title_font, self.content_title_min_font_size), "title")
        longest_page_number: int = self.get_longest_line(ImageFont.truetype(
            self.content_page_number_font, self.content_page_number_font_size), "pages")
        column = longest_title + longest_page_number + self.space_title_to_page_number

        if space_for_column >= column:
            return True
        else:
            return False

    def get_text_size(self, text: str, font: ImageFont.ImageFont) -> tuple:
        text = str(text)
        width = font.getmask(text).getbbox()[2]
        height = font.getmask(text).getbbox()[3]
        if "\n" in text:
            height += height + int(height/3)
            width = width - font.getmask(text[text.find("\n"):]).getbbox()[2]
        return [width, height]


    def get_longest_line(self, font: ImageFont.ImageFont, key: str) -> int:
        lines = list()
        for chapter in self.chapters:
            lines.append(self.get_text_size(chapter.get(key), font)[0])
        return (max(lines))

    def get_highest_line(self, font: ImageFont.ImageFont, key: str) -> int:
        lines = 0
        for chapter in self.chapters:
            lines += self.get_text_size(chapter.get(key), font)[1]
        return (lines)

    def draw_titles(self, resolution: tuple):
        height = self.page_top_margin
        max_width = resolution[0] - \
            self.page_left_margin - self.page_right_margin
        title_text, title_font = self.resize(
            self.title, self.title_font, self.title_font_size, self.title_min_font_size, max_width)
        title_width, title_height = self.get_text_size(title_text, title_font)
        self.temp_height = height + title_height + self.space_title_to_subtitle
        self.draw_text.multiline_text(
            (int(self.img.size[0]/2 - title_width/2), height), title_text, font=title_font, fill=self.title_font_color)

        subtitle_text, subtitle_font = self.resize(
            self.subtitle_text, self.subtitle_font, self.subtitle_font_size, self.subtitle_min_font_size, max_width)
        subtitle_width, subtitle_height = self.get_text_size(
            subtitle_text, subtitle_font)
        self.draw_text.multiline_text(
            (int(self.img.size[0]/2 - subtitle_width/2), self.temp_height), subtitle_text, font=subtitle_font, fill=self.subtitle_font_color)
        self.temp_height += subtitle_height

    def resize(self, text: str, font_path: str, font_size: int, min_font_size: int, max_width: int) -> list:
        font = ImageFont.truetype(font_path, size=font_size)
        if max_width > self.get_text_size(text, font)[0]:
            return [text, font]
        else:
            for iter in range(font_size - min_font_size):
                font = ImageFont.truetype(font_path, size=font_size - iter)
                if max_width > self.get_text_size(text, font)[0]:
                    return [text, font]

            words_list = text.split(" ")
            temp_line = ""
            for word in words_list:
                temp_line = temp_line + word + " "
                if self.get_text_size(temp_line, font)[0] >= max_width:
                    temp_line = temp_line.strip()
                    temp_line = temp_line[:temp_line.rfind(" ")]
                    text = temp_line + "\n" + text[len(temp_line) + 1:]
                    return [text, font]

    def draw_content(self, resolution: tuple):
        self.temp_height += self.space_sibtitle_to_content
        block_width = self.get_longest_line(ImageFont.truetype(
            self.content_title_font, size=self.content_title_font_size), "title")
        page_block = self.get_longest_line(ImageFont.truetype(
            self.content_page_number_font, size=self.content_page_number_font_size), "pages") + self.space_title_to_page_number
        block_width += page_block
        if block_width > resolution[0] - self.page_left_margin - self.page_right_margin:
            block_width = resolution[0] - \
                self.page_left_margin - self.page_right_margin
        left_border = self.page_left_margin

        self.draw(self.chapters, left_border, block_width, page_block, self.content_style_mirror_columns)

    def draw_content_two_columns(self, resolution: tuple):
        self.temp_height += self.space_sibtitle_to_content

        block_width = self.get_longest_line(ImageFont.truetype(
            self.content_title_font, size=self.content_title_font_size), "title")
        page_block = self.get_longest_line(ImageFont.truetype(
            self.content_page_number_font, size=self.content_page_number_font_size), "pages") + self.space_title_to_page_number
        block_width += page_block
        if block_width > int((resolution[0] - self.page_left_margin - self.page_right_margin - self.space_between_columns)/2):
            block_width = int((resolution[0] - self.page_left_margin -
                               self.page_right_margin - self.space_between_columns)/2)
        left_border = self.page_left_margin

        first_column_content: tuple = self.chapters[:int(len(self.chapters)/2)]
        second_column_content: tuple = self.chapters[int(
            len(self.chapters)/2):]
        self.draw(first_column_content, left_border, block_width, page_block)
        left_border = self.page_left_margin + block_width + self.space_between_columns
        self.draw(second_column_content, left_border,
                  block_width, page_block, True)

    def draw(self, chapters: list, left_border: int, block_width: int, page_block: int, mirrored: bool = False):
        self.temp_height += self.space_sibtitle_to_content
        autor_fill = self.content_author_font_color
        title_fill = self.content_title_font_color
        page_num_fill = self.content_page_number_font_color
        temp_height: int = self.temp_height
        if mirrored:
            align: str = "left"
        else:
            align: str = "right"

        for chapter in chapters:
            author: str = chapter.get("author")
            title: str = chapter.get("title")
            pages: str = str(chapter.get("pages"))

            author, author_font = self.resize(
                author, self.content_author_font, self.content_author_font_size, self.content_author_min_font_size, block_width-page_block)
            autor_width, autor_height = self.get_text_size(author, author_font)
            if mirrored:
                author_start_coordinate: int = left_border+page_block
            else:
                author_start_coordinate: int = left_border + \
                    block_width - autor_width - page_block
            self.draw_text.multiline_text(
                (author_start_coordinate, temp_height), author, font=author_font, fill=autor_fill, align=align)
            temp_height += autor_height + self.space_author_to_title

            page_font = ImageFont.truetype(
                self.content_page_number_font, self.content_page_number_font_size)
            page_width = self.get_text_size(pages, page_font)[0]
            if mirrored:
                page_start_coordinate: int = left_border
            else:
                page_start_coordinate: int = left_border+block_width-page_width
            self.draw_text.text((page_start_coordinate,
                                 temp_height), pages, font=page_font, fill=page_num_fill)

            title, title_font = self.resize(
                title, self.content_title_font, self.content_title_font_size, self.content_title_min_font_size, block_width - page_width-page_block)
            title_width, title_height = self.get_text_size(title, title_font)
            if mirrored:
                title_start_coordinate: int = left_border+page_block
            else:
                title_start_coordinate: int = left_border+block_width-title_width-page_block
            self.draw_text.multiline_text(
                (title_start_coordinate, temp_height), title, font=title_font, fill=title_fill, align=align)
            temp_height += title_height + \
                self.space_title_to_autor


if __name__ == "__main__":

    sys.argv = ("/home/tomoko/project/hacker/test/main.py -i /home/tomoko/project/hacker/test/toc.json -o . -n test.jpg -s /home/tomoko/project/hacker/test/settings.json".split(" "))
    page = Create_content_page()
