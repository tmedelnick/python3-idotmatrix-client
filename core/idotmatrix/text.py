import logging
import zlib
from .font5x8 import Font5x8

class Text:
    '''
    Text generally displays some bitmap data.
    Like a black&white GIF with some text and background color.
    
    Following is for a 16x16 display, the app code is not very clear what to set in bitmap_header and header, see below.
    Need to compare the data, which is sent over bluetooth.
    
    
    Bitmap data needs to be 8 pixel wide, 16 pixel high (for 16x16 display)
    
    The app generates bitmap data from painting on a canvas. Font size is fixed to 8x12 (???)
    The app code also contains data for a 5x8 pixel font (which is not used???).
    
    
     Font 5x8 bitmap for character 'A' and 'B' (upper 3 bits always 0)
     | b0| b1| b2| b3| b4| b5| b6| b7|   
    -+-------------------------------+
     | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | Byte0
     | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | Byte1
     | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | Byte2
     | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | Byte3
 A   | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | Byte4
     | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | Byte5
     | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | Byte6
     | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | Byte7
     +-------------------------------+
     | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | Byte8
     | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | Byte9
     | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | Byte10
 B   | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | Byte11
     | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | Byte12
     | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | Byte13
     | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | Byte14
     | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | Byte15
     +-------------------------------+
     
     bitmap data for 16x16 display
     1 character: bitmap height 16 pixel, width 8 pixel
     2 lines of characters with 5x8 pixel font possible
     
     data per character
        Header per character
            bitmap_header = bytearray(
                [
                    0x02,   # bitmap height 16 pixel -> 16 bytes per character (not clear)
                    0xff, 0xff, 0xff, # fixed
                ]
            )
        bitmap data
        
     Header for complete bitmap
     text_header = bytearray(
            [
                1,   # text length lobyte, number of 8 pixel blocks
                0,   # text length hibyte
                0,   # fixed
                1,   # fixed
                0,   # mode (0=fixed, 1=left scrolling, ...) as per App
                50,  # speed 
                1,   # color mode
                255, # color red
                255, # color green
                0,   # color blue
                8,   # background mode
                0,   # background color red
                0,   # background color green
                0,   # background color blue
            ]
        )
     
     chunking like in GIF code
     header = bytearray(
            [
                255,    # chunk length
                255,    # 
                3,      # fixed
                0,      # fixed
                0,      # 0 if first chunk, else 2
                255,    # length payload
                255,    
                255,
                255,
                255,    # CRC
                255,
                255,
                255,
                0,      # works for 16x16, not clear for other sizes 
                0,      # works for 16x16, not clear for other sizes 
                12,     # works for 16x16, not clear for other sizes 
            ]
        )
     
    '''
    logging = logging.getLogger("idotmatrix." + __name__)
    
    
    def split_into_chunks(self, data, chunk_size):
        """Split the data into chunks of specified size.

        Args:
            data (bytearray): data to split into chunks
            chunk_size (int): size of the chunks

        Returns:
            list: returns list with chunks of given data input
        """
        return [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]


    def create_bitmapdata(self, line, max_len):
        font5x8 = Font5x8()
        line_len = len(line)
        bitmap_data = []
        for i in range(max_len):
            charbitmap = font5x8.get_charbitmap(line[i]) if i < line_len else font5x8.get_charbitmap(' ')
            bitmap_data.append(charbitmap)
            
        return bitmap_data

    def create_textdata(self, line1, line2):
        self.logging.info(line1)
        self.logging.info(line2)
        
        line1_len = len(line1)
        line2_len = len(line2)
        
        max_len = max(line1_len, line2_len)
        line1_bitmap = self.create_bitmapdata(line1, max_len)
        line2_bitmap = self.create_bitmapdata(line2, max_len)
        
        text_header = bytearray(
            [
                max_len,   # text length lowbyte
                0,   # text length hibyte
                0,   # fixed
                1,   # fixed
                0,   # mode
                50,  # speed
                1,   # color mode
                255, # color red
                255, # color green
                0,   # color blue
                8,   # background mode
                0,   # background color red
                0,   # background color green
                0,   # background color blue
            ]
        )
        
        bitmap_header = bytearray(
            [0x02, 0xff, 0xff, 0xff,]
        )
        text_bitmap_data = bytearray()
        for i in range(max_len):
            text_bitmap_data +=  bitmap_header + bytearray(line1_bitmap[i]) + bytearray(line2_bitmap[i])
            
        
       
        return text_header + text_bitmap_data

    def create_payloads(self, text_line1, text_line2):
        """Creates payloads from a GIF file.

        Args:
            gif_data (bytearray): data of the gif file

        Returns:
            bytearray: returns bytearray payload
        """
        # TODO: make this function look more nicely :)

        text_data = self.create_textdata(text_line1, text_line2)
        # Calculate CRC of the text data
        crc = zlib.crc32(text_data)
        # header for gif
        header = bytearray(
            [
                255,
                255,
                3,
                0,
                0,
                255,
                255,
                255,
                255,
                255,
                255,
                255,
                255,
                0,
                0,
                12,
            ]
        )
        # set length
        data_len = int(len(text_data) + len(header));
        self.logging.info("length text_data ")
        self.logging.info(data_len)
        
        #header[5:9] = int(len(text_data) + len(header)).to_bytes(4, byteorder="little")
        header[5:9] = int(len(text_data)).to_bytes(4, byteorder="little")
        # add crc
        header[9:13] = crc.to_bytes(4, byteorder="little")
        # Split the GIF data into 4096-byte chunks
        gif_chunks = self.split_into_chunks(text_data, 4096)
        # build data
        payloads = bytearray()
        for i, chunk in enumerate(gif_chunks):
            header[4] = 2 if i > 0 else 0
            chunk_len = len(chunk) + len(header)
            header[0:2] = chunk_len.to_bytes(2, byteorder="little")
            payloads.extend(header + chunk)

        self.logging.info(payloads)

        return payloads
