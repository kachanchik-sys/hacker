from PIL import Image, ImageDraw, ImageFont
import PIL
import json
import sys
import os
import argparse

class Page():

    def __init__(self) -> None:
        parser = argparse.ArgumentParser() 
        parser.add_argument("-i",'--input',required=True, help="Path to json with info", type=str)
        parser.add_argument("-o",'--output',required=True, help="Path where to save the image", type=str)
        parser.add_argument("-n",'--name',required=True, help="Name of img", type=str) 
        parser.add_argument("-s",'--settings',required=True, help="Path to json with settings", type=str) 
        args = parser.parse_args() 
        self.check_console_args(args)

        with open(args.input, "r", encoding="utf-8") as f:
            self.info:dict = json.loads(f.read())

        with open(args.settings, "r", encoding="utf-8") as f:
            self.settings:dict = json.loads(f.read())

        self.img = Image.new("RGB", self.settings["resolution"], color=self.settings["color"])
        self.draw_text = ImageDraw.Draw(self.img)
        self.draw_titles()
        self.draw_content()
        self.img.save(f"{args.output}/{args.name}")
        print("Done!")



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
        


    def text_size(self, text:str, font:ImageFont.ImageFont, is_list:bool = False)-> int:
        text = str(text)
        width = font.getmask(text).getbbox()[2]
        height = font.getmask(text).getbbox()[3]
        return [width, height]



    def get_longest_line(self,font, key)-> int:
        lines = list()
        for chapter in self.info["chapters"]:
            lines.append(self.text_size(chapter.get(key), font)[0])
        return(sorted(lines, reverse=True)[0])



    def resize(self, max_width:int, text:str, settings:dict):
        font = ImageFont.truetype(settings["font"], size = settings["font_size"])
        if max_width > self.text_size(text, font)[0]:
            return [text, font]
        else:
            for font_kegel in range(settings["font_size"] - settings["min_font_size"]):
                    font = ImageFont.truetype("roboto_regular.otf", size = settings["font_size"] - font_kegel)
                    if max_width > self.text_size(text, font)[0]:
                        return [text, font]
            
            words_list = text.split(" ")
            temp_line = ""
            for word in words_list:
                temp_line = temp_line + word + " "
                if self.text_size(temp_line, font)[0] >= max_width:
                    temp_line = temp_line.strip()
                    temp_line = temp_line[:temp_line.rfind(" ")]
                    text = temp_line + "\n" + text[len(temp_line) + 1:]
                    return [text, font]
            

    def draw_titles(self):
        height = self.settings["title"]["gap"]
        max_width = self.settings["resolution"][0] - self.settings["side_borders"] * 2
        title_text, title_font = self.resize(max_width, self.info["title"], self.settings["title"])
        title_width, title_height = self.text_size(title_text, title_font)
        self.temp_height = height + title_height + self.settings["subtitle"]["gap"]
        self.draw_text.multiline_text((int(self.img.size[0]/2 - title_width/2), height), title_text, font=title_font, fill=self.settings["title"]["font_color"])

        
        subtitle_text, subtitle_font = self.resize(max_width, self.settings["subtitle"]["text"], self.settings["subtitle"])
        subtitle_width, subtitle_height = self.text_size(subtitle_text, subtitle_font)
        self.draw_text.multiline_text((int(self.img.size[0]/2 - subtitle_width/2), self.temp_height), subtitle_text, font=subtitle_font, fill=self.settings["subtitle"]["font_color"])        
        self.temp_height += subtitle_height


    def draw_content(self):
        self.temp_height += self.settings["content"]["gap_top"]
        autor_fill =  self.settings["content"]["author"]["font_color"]
        title_fill = self.settings["content"]["title"]["font_color"]
        page_num_fill = self.settings["content"]["pages"]["font_color"]

        #vertical_distance = 15
        block_width = self.get_longest_line(ImageFont.truetype(self.settings["content"]["title"]["font"], size = self.settings["content"]["title"]["font_size"]), "title")
        page_block = self.get_longest_line(ImageFont.truetype(self.settings["content"]["pages"]["font"], size = self.settings["content"]["pages"]["font_size"]), "pages") + self.settings["content"]["title_to_pages_distance"]
        block_width += page_block
        if block_width > self.settings["resolution"][0] - self.settings["side_borders"]*2:
            block_width = self.settings["resolution"][0] - self.settings["side_borders"]*2
        left_border = self.settings["side_borders"]
        
        
        for chapter in self.info["chapters"]:
            author:str = chapter.get("author")
            title:str = chapter.get("title")
            pages:str = str(chapter.get("pages"))

            author, author_font = self.resize(block_width-page_block, author, self.settings["content"]["author"])
            autor_width, autor_height = self.text_size(author, author_font)
            self.draw_text.multiline_text((left_border+block_width-autor_width-page_block, self.temp_height),author, font=author_font, fill = autor_fill)
            self.temp_height += autor_height + self.settings["content"]["author_to_title_distance"]

            page_font = ImageFont.truetype(self.settings["content"]["pages"]["font"], self.settings["content"]["pages"]["font_size"])
            page_width, page_height = self.text_size(pages, page_font)
            self.draw_text.text((left_border+block_width-page_width, self.temp_height),pages, font=page_font, fill = page_num_fill)
            
            title, title_font = self.resize(block_width - page_width-page_block, title, self.settings["content"]["title"])
            title_width, title_height = self.text_size(title, title_font)
            self.draw_text.multiline_text((left_border+block_width-title_width-page_block, self.temp_height),title, font=title_font, fill = title_fill)
            self.temp_height += title_height + self.settings["content"]["title_to_author_distance"]

        


if __name__ == "__main__":
    
    page = Page()