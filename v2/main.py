from PIL import Image, ImageDraw, ImageFont
import math
import json
import os
import argparse
import sys

class Create_content_page():

    def __init__(self):
        """Generate and save contents page from json
        """
        args = self.create_console_args()
        self.read_content_json(args.input)
        self.read_settings_json(args.settings)
        img = self.draw_page()
        img.save(f"{args.output}/{args.name}")
        print("Done!")

    def create_console_args(self) -> argparse.Namespace:
        """Creates an interface for requesting arguments from the console

        Returns:
            argparse.Namespace: entered arguments
        """
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

    def check_console_args(self, args:argparse.Namespace) -> None:
        """Checks the entered arguments for validity

        Args:
            args (argparse.Namespace):
        """
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

    def read_content_json(self, path: str) -> None:
        """Reads json file containing the contents of the volume

        Args:
            path (str): conditional or full path to the file
        """
        with open(path, "r", encoding="utf-8") as f:
            content: dict = json.loads(f.read())

        self.title: str = content["title"]
        self.chapters: tuple = content["chapters"]

    def read_settings_json(self, path: str) -> None:
        """Reads json file containing the page generation settings

        Args:
            path (str): conditional or full path to the file
        """

        with open(path, "r", encoding="utf-8") as f:
            settings: dict = json.loads(f.read())
            self.settings: dict = settings

    def draw_page(self) -> Image.Image:
        """High-level method of page rendering

        Returns:
            Image.Image: The image object
        """
        page_width: int = self.settings["page"]["resolution"][0]
        page_height: int = self.settings["page"]["resolution"][1]
        
        if page_width == "auto" and page_height == "auto":
            render_resolution = [
                self.dynamic_width_calc(), self.dynamic_height_calc()]
        elif page_width == "auto":
            render_resolution = [
                self.dynamic_width_calc(), page_height]
        elif page_height == "auto":
            render_resolution = [page_width,
                                 self.dynamic_height_calc()]
        else:
            render_resolution: dict = [page_width, page_height]

        if self.settings["page"]["target_aspect_ratio"]:
            render_resolution = self.calculate_output_resolution(render_resolution)

        self.img = Image.new("RGB", render_resolution, color=self.settings["page"]["color"])
        self.draw_text = ImageDraw.Draw(self.img)

        if self.settings["content"]["style"]["use_two_columns"] and self.is_enough_space_for_two_columns(render_resolution):
            self.draw_titles(render_resolution)
            self.draw_content_two_columns(render_resolution)

        else:
            self.draw_titles(render_resolution)
            self.draw_content(render_resolution)

        return self.img

    def dynamic_width_calc(self) -> int:
        """Automatically adjusts the page width

        Returns:
            int: width
        """
        longest_title: int = self.get_longest_line(ImageFont.truetype(
            self.settings["content"]["title"]["font"], self.settings["content"]["title"]["font_size"]), "title")
        longest_page_number: int = self.get_longest_line(ImageFont.truetype(
            self.settings["content"]["page_number"]["font"], self.settings["content"]["page_number"]["font_size"]), "pages")

        content_block_width: int = self.settings["space"]["title_to_page_number"]
        if self.settings["content"]["style"]["use_two_columns"]:
            content_block_width += int((longest_title + longest_page_number)
                                       * 2 + self.settings["space"]["between_columns"])
        else:
            content_block_width += longest_title + longest_page_number

        title_width = self.get_text_size(self.title, ImageFont.truetype(
            self.settings["title"]["font"], self.settings["title"]["font_size"]))[0]
        subtitle_width = self.get_text_size(self.settings["subtitle"]["text"], ImageFont.truetype(
            self.settings["subtitle"]["font"], self.settings["subtitle"]["font_size"]))[0]

        return max([content_block_width, title_width, subtitle_width]) + self.settings["page"]["left_margin"] + self.settings["page"]["right_margin"]

    def dynamic_height_calc(self) -> int:
        """Automatically adjusts the page height

        Returns:
            int: height
        """
        title_height = self.get_text_size(self.title, ImageFont.truetype(
            self.settings["title"]["font"], self.settings["title"]["font_size"]))[1]
        subtitle_height = self.get_text_size(self.settings["subtitle"]["text"], ImageFont.truetype(
            self.settings["subtitle"]["font"], self.settings["subtitle"]["font_size"]))[1]
        page_height: int = self.settings["page"]["top_margin"] + self.settings["page"]["bottom_margin"] + \
            self.settings["space"]["title_to_subtitle"] + self.settings["space"]["sibtitle_to_content"] + title_height + subtitle_height
        highest_author = self.get_hight_of_lines(ImageFont.truetype(
            self.settings["content"]["author"]["font"], self.settings["content"]["author"]["font_size"]), "author")
        highest_title = self.get_hight_of_lines(ImageFont.truetype(
            self.settings["content"]["title"]["font"], self.settings["content"]["title"]["font_size"]), "title")

        if self.settings["content"]["style"]["use_two_columns"] and self.is_enough_space_for_two_columns([self.dynamic_width_calc(), 0]):
            page_height += math.ceil((highest_author + highest_title) / 2) + (self.settings["space"]["author_to_title"] + self.settings["space"]["title_to_autor"]) * math.ceil(len(self.chapters)/2) - self.settings["space"]["title_to_autor"]
        else:
            page_height += highest_author + highest_title + (self.settings["space"]["author_to_title"] +
                                                             self.settings["space"]["title_to_autor"]) * len(self.chapters) - self.settings["space"]["title_to_autor"]
        return page_height

    def calculate_output_resolution(self, input_resolution: tuple):
        """Get scaled w/h of image for passed w_ration/h_ration
        E.g.:
            50x200 with ratio 1x2 -> 100x200
            150x200 with ratio 1x2 -> 150x300
        Return:
            tuple: resolution
        """
        img_width: int = input_resolution[0]
        img_height: int = input_resolution[1]
        w_ratio: int = self.settings["page"]["target_aspect_ratio"][0]
        h_ratio: int = self.settings["page"]["target_aspect_ratio"][1]
        new_width: int = img_width
        new_height: int = img_height

        horizontal_pixels_per_ratio: int = math.ceil(img_width / w_ratio)
        vertical_pixels_per_ratio: int = math.ceil(img_height / h_ratio)

        required_height: int = h_ratio * horizontal_pixels_per_ratio
        required_width: int = w_ratio * vertical_pixels_per_ratio

        if required_height > img_height:
            new_height = required_height

        if required_width > img_width:
            new_width = required_width
        
        return [new_width, new_height]

    def is_enough_space_for_two_columns(self, render_resolution: int) -> bool:
        """Checks if there is enough space for two columns 

        Args:
            render_resolution (int): Img resolution

        Returns:
            bool: True if enough or False if not enough 
        """
        dead_space: int = self.settings["page"]["left_margin"] + \
            self.settings["page"]["right_margin"] + self.settings["space"]["between_columns"]
        space_for_column = int((render_resolution[0] - dead_space) / 2)

        longest_title: int = self.get_longest_line(ImageFont.truetype(
            self.settings["content"]["title"]["font"], self.settings["content"]["title"]["min_font_size"]), "title")
        longest_page_number: int = self.get_longest_line(ImageFont.truetype(
            self.settings["content"]["page_number"]["font"], self.settings["content"]["page_number"]["font_size"]), "pages")
        column = longest_title + longest_page_number + self.settings["space"]["title_to_page_number"]

        if space_for_column >= column:
            return True
        else:
            return False

    def get_text_size(self, text: str, font: ImageFont.ImageFont) -> tuple:
        """Calculates how much width and height the text will take with the specified background

        Args:
            text (str): Text for calculate
            font (ImageFont.ImageFont): Font for calculate

        Returns:
            tuple: [Width, Height]
        """
        text = str(text)
        width = font.getmask(text).getbbox()[2]
        height = font.getmask(text).getbbox()[3]
        if "\n" in text:
            height += height + int(height/3)
            width = width - font.getmask(text[text.find("\n"):]).getbbox()[2]
        return [width, height]


    def get_longest_line(self, font: ImageFont.ImageFont, key: str) -> int:
        """Returns the width of the longest line with the specified font

        Args:
            font (ImageFont.ImageFont): Font for calculate
            key (str): key of tuple

        Returns:
            int: Width
        """
        lines = list()
        for chapter in self.chapters:
            lines.append(self.get_text_size(chapter.get(key), font)[0])
        return (max(lines))

    def get_hight_of_lines(self, font: ImageFont.ImageFont, key: str) -> int:
        lines = 0
        for chapter in self.chapters:
            lines += self.get_text_size(chapter.get(key), font)[1]
        return (lines)

    def draw_titles(self, resolution: tuple):
        height = self.settings["page"]["top_margin"]
        max_width = resolution[0] - \
            self.settings["page"]["left_margin"] - self.settings["page"]["right_margin"]
        title_text, title_font = self.resize(
            self.title, self.settings["title"]["font"], self.settings["title"]["font_size"], self.settings["title"]["min_font_size"], max_width)
        title_width, title_height = self.get_text_size(title_text, title_font)
        self.temp_height = height + title_height + self.settings["space"]["title_to_subtitle"]
        self.draw_text.multiline_text(
            (int(self.img.size[0]/2 - title_width/2), height), title_text, font=title_font, fill=self.settings["title"]["font_color"])

        subtitle_text, subtitle_font = self.resize(
            self.settings["subtitle"]["text"], self.settings["subtitle"]["font"], self.settings["subtitle"]["font_size"], self.settings["subtitle"]["min_font_size"], max_width)
        subtitle_width, subtitle_height = self.get_text_size(
            subtitle_text, subtitle_font)
        self.draw_text.multiline_text(
            (int(self.img.size[0]/2 - subtitle_width/2), self.temp_height), subtitle_text, font=subtitle_font, fill=self.settings["subtitle"]["font_color"])
        self.temp_height += subtitle_height
        self.temp_height += self.settings["space"]["sibtitle_to_content"]

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
        page_block = self.get_longest_line(ImageFont.truetype(
            self.settings["content"]["page_number"]["font"], size=self.settings["content"]["page_number"]["font_size"]), "pages") + self.settings["space"]["title_to_page_number"]
        left_border = self.settings["page"]["left_margin"]
        
        if self.settings["content"]["style"]["align"].lower().strip() == "right":
            block_width = resolution[0] - self.settings["page"]["left_margin"] - self.settings["page"]["right_margin"]
            if self.settings["content"]["style"]["mirror_columns"]:
              left_border = self.get_longest_line(ImageFont.truetype(
                    self.settings["content"]["title"]["font"], size=self.settings["content"]["title"]["font_size"]), "title") + page_block
                
        else:
            block_width = self.get_longest_line(ImageFont.truetype(
            self.settings["content"]["title"]["font"], size=self.settings["content"]["title"]["font_size"]), "title") + page_block
            if block_width > resolution[0] - self.settings["page"]["left_margin"] - self.settings["page"]["right_margin"]:
                block_width = resolution[0] - \
                    self.settings["page"]["left_margin"] - self.settings["page"]["right_margin"]

        

        self.draw(self.chapters, left_border, block_width, page_block, self.settings["content"]["style"]["mirror_columns"])

    def draw_content_two_columns(self, resolution: tuple):
        self.temp_height += self.settings["space"]["sibtitle_to_content"]

        block_width = self.get_longest_line(ImageFont.truetype(
            self.settings["content"]["title"]["font"], size=self.settings["content"]["title"]["font_size"]), "title")
        page_block = self.get_longest_line(ImageFont.truetype(
            self.settings["content"]["page_number"]["font"], size=self.settings["content"]["page_number"]["font_size"]), "pages") + self.settings["space"]["title_to_page_number"]
        block_width += page_block
        if block_width > int((resolution[0] - self.settings["page"]["left_margin"] - self.settings["page"]["right_margin"] - self.settings["space"]["between_columns"])/2):
            block_width = int((resolution[0] - self.settings["page"]["left_margin"] -
                               self.settings["page"]["right_margin"] - self.settings["space"]["between_columns"])/2)
        left_border = self.settings["page"]["left_margin"]

        first_column_content: tuple = self.chapters[:int(len(self.chapters)/2)]
        second_column_content: tuple = self.chapters[int(
            len(self.chapters)/2):]
        self.draw(first_column_content, left_border, block_width, page_block)
        left_border = self.settings["page"]["left_margin"] + block_width + self.settings["space"]["between_columns"]
        self.draw(second_column_content, left_border,
                  block_width, page_block, True)

    def draw(self, chapters: list, left_border: int, block_width: int, page_block: int, mirrored: bool = False):
        self.temp_height += self.settings["space"]["sibtitle_to_content"]
        autor_fill = self.settings["content"]["author"]["font_color"]
        title_fill = self.settings["content"]["title"]["font_color"]
        page_num_fill = self.settings["content"]["page_number"]["font_color"]
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
                author, self.settings["content"]["author"]["font"], self.settings["content"]["author"]["font_size"], self.settings["content"]["author"]["min_font_size"], block_width-page_block)
            autor_width, autor_height = self.get_text_size(author, author_font)
            if mirrored:
                author_start_coordinate: int = left_border+page_block
            else:
                author_start_coordinate: int = left_border + \
                    block_width - autor_width - page_block
            self.draw_text.multiline_text(
                (author_start_coordinate, temp_height), author, font=author_font, fill=autor_fill, align=align)
            temp_height += autor_height + self.settings["space"]["author_to_title"]

            page_font = ImageFont.truetype(
                self.settings["content"]["page_number"]["font"], self.settings["content"]["page_number"]["font_size"])
            page_width = self.get_text_size(pages, page_font)[0]
            if mirrored:
                page_start_coordinate: int = left_border
            else:
                page_start_coordinate: int = left_border+block_width-page_width
            self.draw_text.text((page_start_coordinate,
                                 temp_height), pages, font=page_font, fill=page_num_fill)

            title, title_font = self.resize(
                title, self.settings["content"]["title"]["font"], self.settings["content"]["title"]["font_size"], self.settings["content"]["title"]["min_font_size"], block_width - page_width-page_block)
            title_width, title_height = self.get_text_size(title, title_font)
            if mirrored:
                title_start_coordinate: int = left_border+page_block
            else:
                title_start_coordinate: int = left_border+block_width-title_width-page_block
            self.draw_text.multiline_text(
                (title_start_coordinate, temp_height), title, font=title_font, fill=title_fill, align=align)
            temp_height += title_height + \
                self.settings["space"]["title_to_autor"]


if __name__ == "__main__":

    sys.argv = ("/home/tomoko/project/hacker/v2/main.py -i /home/tomoko/project/hacker/v2/toc.json -o . -n test.jpg -s /home/tomoko/project/hacker/v2/settings.json".split(" "))
    page = Create_content_page()
