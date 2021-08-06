import glob
import json
import os
from datetime import datetime

import cv2
import imutils
from imutils import contours
from skimage.metrics import normalized_root_mse

OUTPUT_DIR = 'envive_helper_python/output/'


def _union(a, b):
    x = min(a[0], b[0])
    y = min(a[1], b[1])
    w = max(a[0]+a[2], b[0]+b[2]) - x
    h = max(a[1]+a[3], b[1]+b[3]) - y
    return [x, y, w, h]


def _intersect(a, b):
    x = max(a[0], b[0])
    y = max(a[1], b[1])
    w = min(a[0]+a[2], b[0]+b[2]) - x
    h = min(a[1]+a[3], b[1]+b[3]) - y
    if h < 0:  # in original code :  if w < 0 or h < 0:
        return False
    return True


def _group_rectangles(rec):
    """
    Uion intersecting rectangles.
    Args:
        rec - list of rectangles in form [x, y, w, h]
    Return:
        list of grouped ractangles
    """
    tested = [False for i in range(len(rec))]
    final = []
    i = 0
    while i < len(rec):
        if not tested[i]:
            j = i+1
            while j < len(rec):
                if not tested[j] and _intersect(rec[i], rec[j]):
                    rec[i] = _union(rec[i], rec[j])
                    tested[j] = True
                    j = i
                j += 1
            final += [rec[i]]
        i += 1

    return final


class ImageMatcher():
    def __init__(self, source_path=None, meta_path=None):
        self.source_path = source_path
        self.meta_obj = self.load_meta_json(meta_path)

    def load_meta_json(self, meta_path=None):
        meta_obj = {}
        if meta_path:
            with open(meta_path) as f:
                meta_obj = json.loads(f.read())
        return meta_obj

    def read_image(self, path):
        originalImage = cv2.imread(path)
        grayImage = cv2.cvtColor(originalImage, cv2.COLOR_BGR2GRAY)
        (thresh, blackAndWhiteImage) = cv2.threshold(grayImage, 160, 255, cv2.THRESH_BINARY)
        return blackAndWhiteImage

    def match_image(self, position_x, position_y, screenshots_path):
        method = cv2.TM_SQDIFF_NORMED

        input_coordinate = (int(position_x), int(position_y))
        # source_path = 'source'
        # screenshots_path = 'screenshots/1.png'
        # input_coordinate = (200, 500)

        # Read the images from the file
        paths = glob.glob(os.path.join(self.source_path, '*', '*.png'))
        source_images = {}
        for path in paths:
            head, tail = os.path.split(path)
            _, tag = os.path.split(head)
            # tag = path.split('/')[1]
            source_images[tag] = self.read_image(path)

        screenshot = cv2.imread(screenshots_path)

        tmp_image = screenshot
        target_image = screenshot
        target_image = cv2.cvtColor(target_image, cv2.COLOR_BGR2GRAY)
        target_image = cv2.threshold(target_image, 10, 255, cv2.THRESH_BINARY_INV)[1]
        screenshot_height, screenshot_width = target_image.shape

        cnts = cv2.findContours(target_image.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(tmp_image, cnts[0], -1, (0, 0, 255), 3)
        cv2.imwrite(os.path.join(OUTPUT_DIR, 'after-draw-contours.png'), tmp_image)

        cnts = imutils.grab_contours(cnts)
        (cnts, bounding_boxes) = contours.sort_contours(cnts, method="left-to-right")

        match_tags = []
        tmp_image = screenshot
        new_bounding_boxes = []
        for index, bounding_box in enumerate(bounding_boxes):
            x, y, w, h = bounding_box
            x = max(x - 6, 0)
            y = max(y - 6, 0)
            w = min(int(w + 12), screenshot_width - x - 1)
            h = min(int(h + 12), screenshot_height - y - 1)

            if w/h < 1 or h <= 23 or w > 130 or h > 130:
                continue

            new_bounding_boxes.append(bounding_box)

        bounding_boxes = list(new_bounding_boxes)
        bounding_boxes = _group_rectangles(bounding_boxes)

        for index, bounding_box in enumerate(bounding_boxes):
            x, y, w, h = bounding_box
            x = max(x - 6, 0)
            y = max(y - 6, 0)
            w = min(int(w + 12), screenshot_width - x - 1)
            h = min(int(h + 12), screenshot_height - y - 1)

            cv2.rectangle(tmp_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

            partial_image = target_image[y:y + h, x:x + w]
            # cv2.imwrite(os.path.join(OUTPUT_DIR, f'bounding_box_{index}.png'), partial_image)

            min_error = 10000000
            match_tag = None
            for tag, source_image in source_images.items():
                resized_partial_image = cv2.resize(partial_image, (source_image.shape[1], source_image.shape[0]))
                # cv2.imwrite(os.path.join(OUTPUT_DIR, f'tag_{tag}.png'), source_image)
                error = normalized_root_mse(source_image, resized_partial_image)
                if error < min_error:
                    min_error = error
                    match_tag = tag

            # print(min_error)
            if min_error < 0.7:
                cv2.imwrite(os.path.join(OUTPUT_DIR, f'partial_image-{index}-{match_tag}-{min_error}.png'), partial_image)
                if input_coordinate[1] >= y and input_coordinate[1] <= y+h:
                    match_tags.append(match_tag)
        print('paaaaaaaaaaaath')
        print((os.path.join(OUTPUT_DIR, f'partial_image-{index}-{match_tag}-{min_error}.png')))
        cv2.circle(tmp_image, input_coordinate, radius=0, color=(255, 0, 0), thickness=30)
        output_path = os.path.join(OUTPUT_DIR, f'{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}_{"-".join(match_tags)}.png')
        cv2.imwrite(output_path, tmp_image)
        match_tags = list(set(match_tags))
        return match_tags
    
    def match_by_meta(self, position_x, position_y):
        match_tags = []
        for tag, meta in self.meta_obj.items():
            if position_x >= meta['x'] and position_x <= meta['x'] + meta['w'] and position_y >= meta['y'] and position_y <= meta['y'] + meta['h']:
                match_tags.append(tag)

        return match_tags


if __name__ == '__main__':
    image_matcher = ImageMatcher(source_path='./source', meta_path='./source/meta.json')
    match_tags = image_matcher.match_image(322, 500, './screenshots/1.png')
    print(match_tags)
    match_tags = image_matcher.match_by_meta(322, 500)
    print(match_tags)
