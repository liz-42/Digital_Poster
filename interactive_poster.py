import pymupdf
import subprocess
import serial
from scipy.spatial import distance
from sentence_transformers import SentenceTransformer


### SETUP ###

# name of poster file to open
poster_file = "C:/Users/daunt/Documents/CreativityTools/ESSbots_Poster.pdf"
# file with plain text of poster
text_file = "C:/Users/daunt/Documents/CreativityTools/ESSbotsPoster.txt"

# browser paths to open pdf in firefox or chrome
browser_path = "C:\\Program Files\\Mozilla Firefox\\firefox.exe"
pdf_path = "file:///C:/Users/daunt/Documents/CreativityTools/ESSbots_Poster.pdf"

# Possible IDs for rfid cards, and associated knowledge mappings
card_mappings = {"032D501C": {"Homeomorphism": "Mathematical function or mapping that preserves properties", # topology
                       "Group": "Mathematical set of elements and actions on those elements", # group theory
                       "Functor": "Structure preserving mapping between mathematical concepts or categories"}, # category theory
                 "73028DFA": {"Choreography": "A set of artistic movements or actions", # dance
                       "Body postures": "Physical position of the body", # dance, acting
                       "Blocking": "Actor locations on stage"} # acting
                       }

### RUN ON STARTUP ###

# open pdf
doc = pymupdf.open(poster_file)
page = doc[0] # pdfs should be one page only, or the poster should be on the first page

print("poster opened")

# read simplified poster text
text = ''
f = open(text_file, "r")
for x in f:
    text = text + x
f.close()

print("text read")
# convert to list of sentences
stripped_text = text.strip().split("\n")

# open serial port
serial_port = serial.Serial("COM6", 9600)

card_id = None
prev_id = "No card in range"

# setup model
model = SentenceTransformer('all-MiniLM-L6-v2')

# functions to process poster sentences
def run_similarity(sentences, corpus):
    '''
    :param sentences: dictionary of knowledge definitions
    :param corpus: list of all sentences in the poster
    :return: list of tuples (score, sentence) sorted by similarity score
    '''
    similarity_scores = []
    for key in sentences:
        key_sim_scores = []
        for sent in corpus:
            encoded_sentence = model.encode([sentences[key]])[0]
            similarity_score = 1 - distance.cosine(encoded_sentence, model.encode([sent])[0])
            key_sim_scores.append(similarity_score)
        # sort the scores
        sentence_pairs = [(key_sim_scores[i], corpus[i], key) for i in range(len(corpus))]
        similarity_scores.extend(sorted(sentence_pairs, reverse=True))
    # final sort
    sorted_similarity_scores = sorted(similarity_scores, reverse=True)
    return sorted_similarity_scores

def select_top_5(sentences):
    '''
    :param sentences: list of tuples (score, sentence)
    :return: list of top 5 most similar sentences
    '''
    top_5 = []

    for val in sentences:
        if val[1] not in top_5 and len(top_5) < 5:
            top_5.append(val[1])
    return top_5

### LOOP ###

while True:
    if serial_port.in_waiting != 0:
        card_id = serial_port.readline().strip().decode("ascii")
        if card_id != prev_id:
            # check if card id is in the list of avail ids
            if card_id in card_mappings.keys():
                print("updating poster")
                # turn on yellow LED to show it's working - send code 1 to serial output
                serial_port.write(str.encode('1'))
                # print result
                result = run_similarity(card_mappings[card_id], stripped_text)
                top_5s = select_top_5(result)

                # add highlights
                sentence_num = 0
                for sentence in top_5s:
                    rects = page.search_for(sentence)
                    if sentence_num == 0:
                        colour = pymupdf.pdfcolor["green"] # indicate top match with green colour
                    else:
                        colour = pymupdf.pdfcolor["yellow"]

                    annot = page.add_highlight_annot(rects)  # highlight it
                    annot.set_colors(stroke=colour)  # change default color
                    annot.update()
                    sentence_num += 1

                # save result
                doc.saveIncr()

                # open in firefox
                p = subprocess.Popen([browser_path, pdf_path], shell=False, stdout=subprocess.PIPE)
                p.wait()  # opens a new page with the saved pdf

                # turn off yellow led
                serial_port.write(str.encode('0'))

            elif card_id == "No card in range":
                print("restore poster")
                # clear annotations
                doc.xref_set_key(page.xref, "Annots", "null")
                # save result
                doc.saveIncr()

                # open in firefox
                p = subprocess.Popen([browser_path, pdf_path], shell=False, stdout=subprocess.PIPE)
                p.wait()  # opens a new page with the saved pdf
            prev_id = card_id
