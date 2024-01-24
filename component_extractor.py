import utils
import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage.filters import threshold_sauvola
import tensorflow as tf
from tqdm import tqdm



class ComponentExtractor:

    def __init__(self, num_chars, min_area=100, max_area=5000, min_dim=10, verbose=False, plot=True):
        self.verbose = verbose
        self.plot = plot
        self.min_area = min_area
        self.max_area = max_area
        self.min_dim = min_dim
        self.img_draw = []
        self.model = tf.keras.models.load_model("my_model.keras")
        self.num_chars = num_chars

    def predict(self, img, dim=(30, 30)):
        img = cv2.resize(img, dim, interpolation=cv2.INTER_NEAREST)
        return self.model((img / 255).reshape(1, *dim, 1))[0]

    def extract(self, img_path):
        self.img_org = cv2.imread(img_path)
        self.img_gray = cv2.cvtColor(self.img_org, cv2.COLOR_BGR2GRAY)
        self.img_crop = self.img_org.copy()
        
        #self.img_bin = cv2.threshold(self.img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        self.img_bin = 255 - (255 * (self.img_gray >= threshold_sauvola(self.img_gray)).astype(np.uint8))
        height, width = self.img_bin.shape
        ratio = 0.15
        height_cutoff = int(height * ratio)
        width_cutoff = int(width * ratio)
        self.img_bin[height_cutoff:height-height_cutoff, width_cutoff:width-width_cutoff] = 0

        self.total_comp, self.pixel_labels, self.comp_info, _ = cv2.connectedComponentsWithStatsWithAlgorithm(self.img_bin, 4, cv2.CV_32S, cv2.CCL_GRANA) #cv2.connectedComponentsWithStats(self.img_bin, 4, cv2.CV_32S)
        print("Done")

        return self._get_comp_imgs()
    
    def get_drawing(self, show=True):
        # if self.cols is None:
        #     print("No drawing made, turn on verbose.")
        #     return None
        
        if show:
            fig, ax = plt.subplots(1, 4)
            ax[0].imshow(self.img_org)
            ax[1].imshow(self.img_crop)
            ax[2].imshow(self.rows, cmap="gray")
            ax[3].imshow(self.img_comps, cmap="gray")
            plt.show()

        return self.cols
    
    def make_crop(self):
        height, width = self.cols.shape

        cols_sums = self.cols.sum(axis=0)
        rows_sums = self.rows.sum(axis=1)

        cols_best_line = np.argmax(cols_sums)
        cols_best_count = cols_sums[cols_best_line] / 255
        rows_best_line = np.argmax(rows_sums)
        rows_best_count = rows_sums[rows_best_line] / 255

        # times 2 since we have two sets of parallel lines for a rect bounding box
        if max(rows_best_count, cols_best_count) < (self.num_chars * 2):
            if self.verbose:
                print("No annotation found")
            return self.img_crop

        axis, is_row, dim = (self.rows, True, height) if rows_best_count > cols_best_count else (self.cols, False, width)

        # draw lines to find contour (not for debug)
        cv2.line(self.cols, (cols_best_line, 0), (cols_best_line, height - 1), (255, 255, 255), 1)
        cv2.line(self.rows, (0, rows_best_line), (width - 1, rows_best_line), (255, 255, 255), 1)

        # find largest contour
        contours, _ = cv2.findContours(axis, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        largest_contour = max(contours, key = cv2.contourArea)
        contour_x, contour_y, contour_width, contour_height = cv2.boundingRect(largest_contour)

        min_lines = contour_y, contour_y + contour_height if is_row else contour_x, contour_x + contour_width
        min_lines = np.array(min_lines)
        cut_line_idx = np.argmin(np.abs(min_lines - (dim / 2)))
        cut_line = min_lines[cut_line_idx]

        min_idx, max_idx = (cut_line, dim) if (dim / 2) > cut_line else (0, cut_line)

        self.img_crop = self.img_crop[min_idx:max_idx, :] if is_row else self.img_crop[:, min_idx:max_idx]

        if self.plot:
            cv2.rectangle(self.img_org, (contour_x, contour_y),
                          (contour_x + contour_width, contour_y + contour_height), (0, 255, 0), 3)
            
        return self.img_crop


    def _get_comp_imgs(self):
        # storing all comps can max out memory
        comp_ls = []
  
        self.cols = np.zeros(self.img_bin.shape, dtype=np.uint8)
        self.rows = np.zeros(self.img_bin.shape, dtype=np.uint8)

        if self.plot:
            self.img_comps = np.zeros(self.img_bin.shape, dtype=np.uint8)
        
        for i in range(1, self.total_comp): 
            
            area = self.comp_info[i, cv2.CC_STAT_AREA]
            x, y = self.comp_info[i, cv2.CC_STAT_LEFT], self.comp_info[i, cv2.CC_STAT_TOP]
            width, height = self.comp_info[i, cv2.CC_STAT_WIDTH], self.comp_info[i, cv2.CC_STAT_HEIGHT]
            
            if (area > self.min_area) and (area < self.max_area) and min(width, height) > self.min_dim: 
                comp_mask = (self.pixel_labels == i).astype(np.uint8) * 255
                comp_img = comp_mask[y:y+height, x:x+width]

                # plt.imshow(comp_img)
                # plt.show()
                # exit()
                if max(width, height) > 100:
                    continue
                #comp_ls.append(comp_img)
                prediction = (self.predict(comp_img).numpy() > 0.5)[0]
                if not prediction:

                    if self.plot:
                        self.img_comps = cv2.bitwise_or(self.img_comps, comp_mask)
                    #cv2.rectangle(self.img_draw, (x, y), (x + width, y + height), (255, 255, 255), 1)

                    cv2.line(self.cols, (x, y), (x+width, y), (255, 255, 255), 1)
                    cv2.line(self.cols, (x, y+height), (x+width, y+height), (255, 255, 255), 1)

                    cv2.line(self.rows, (x, y), (x, y+height), (255, 255, 255), 1)
                    cv2.line(self.rows, (x+width, y), (x+width, y+height), (255, 255, 255), 1)
                    #print(x, y)
        
        self.make_crop()


        return comp_ls



if __name__ == "__main__":
    path ="../datasets/annotations/IRHT_P_002497_ant.tif"
    path = "../datasets/ICDAR2017_CLaMM_Training/IRHT_P_002307.tif" #IRHT_P_002753.tif"
    #path = "../ICDAR2017_CLaMM_task2_task4/315556101_MS0894_0104.jpg"
    comp_extract = ComponentExtractor(verbose=True)
    comp_extract.extract(path)
    img = comp_extract.get_drawing()

