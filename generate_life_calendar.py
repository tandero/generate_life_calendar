import datetime
import argparse
import sys
import os
import cairo  # from pycairo, i.e. install pycairo if missing


# Configuration
DOC_NAME = "life_calendar.pdf"
PAST_DATE = datetime.datetime.strptime('14/12/2021', '%d/%m/%Y')

# PDF conversion factors
#  DOC_WIDTH and DOC_HEIGHT units are "points"
#  360 points = 5 inches = 127 mm  
MM_TO_PT = 360/127
IN_TO_PT = 360/5
PT_TO_MM = 127/360
PT_TO_IN = 5/360

#  Paper size
PAPER = 0      # Debug
if(PAPER == 1):
    # A1 standard international paper size
    DOC_WIDTH_MM = 594  
    DOC_HEIGHT_MM = 841
    DOC_WIDTH = DOC_WIDTH_MM*MM_TO_PT
    DOC_HEIGHT = DOC_HEIGHT_MM*MM_TO_PT
elif(PAPER == 4):
    # A4 standard international paper size
    DOC_WIDTH_MM = 210
    DOC_HEIGHT_MM = 297
    DOC_WIDTH = DOC_WIDTH_MM*MM_TO_PT
    DOC_HEIGHT = DOC_HEIGHT_MM*MM_TO_PT
else:
    # 8.5 x 11 paper size
    DOC_WIDTH_IN = 8.5
    DOC_HEIGHT_IN = 11
    DOC_WIDTH = DOC_WIDTH_IN*IN_TO_PT
    DOC_HEIGHT = DOC_HEIGHT_IN*IN_TO_PT 

LANDSCAPE = False
if(LANDSCAPE):
    DOC_WIDTH,DOC_HEIGHT = DOC_HEIGHT,DOC_WIDTH


# Grid
#  Fitted empirically to arbitrary multiplicative factor describing 
#   the relation between (the height of the page) and (the total vertical margin) 
#   ARBIT_GRID_Y_FACTOR describes the proportion of the page that is margin 
#   used to calculate margin, spacing between boxes, box line width, and (eventually) box dimensions 
#   Doesn't have to be symmetric, but it is right now
ARBIT_GRID_FACTOR = 1/(2**5)    #print(1/ARBIT_GRID_FACTOR)
GRID_Y_MARGIN = DOC_HEIGHT*ARBIT_GRID_FACTOR
GRID_X_MARGIN = DOC_WIDTH*ARBIT_GRID_FACTOR

GRID_HEIGHT = DOC_HEIGHT - (GRID_Y_MARGIN*2)
GRID_WIDTH = DOC_WIDTH - (GRID_X_MARGIN*2)


# NUM_YEARS can be passed in as a target age between MIN_AGE and MAX_AGE; otherwise, it will default to DEFAULT_AGE
NUM_YEARS = 90
DEFAULT_AGE = 90
MIN_AGE = 60
MAX_AGE = 120
# NUM_WEEKS is 53 to allow for the odd year with 53 weeks
NUM_WEEKS = 53


# Define boxes
#   Define spacing between boxes
ARBIT_SPACING_FACTOR = 1/(2**9)
GRID_SPACING = DOC_HEIGHT*ARBIT_SPACING_FACTOR
#print(GRID_SPACING)

#  Define box lines
ARBIT_LINE_FACTOR = 1/(2**10)
BOX_LINE_WIDTH = DOC_HEIGHT*ARBIT_LINE_FACTOR
#print(BOX_LINE_WIDTH)

# Define size of boxes
if(LANDSCAPE):
    BASE_BOX_SIZE = (GRID_WIDTH / NUM_YEARS) - GRID_SPACING
    GRID_Y_MARGIN = (DOC_HEIGHT - ((BASE_BOX_SIZE + GRID_SPACING) * NUM_WEEKS)) / 2
else:
    BASE_BOX_SIZE = (GRID_HEIGHT / NUM_YEARS) - GRID_SPACING
    GRID_X_MARGIN = (DOC_WIDTH - ((BASE_BOX_SIZE + GRID_SPACING) * NUM_WEEKS)) / 2

# GRID_WIDTH / NUM_YEARS = BASE_BOX_SIZE + GRID_SPACING


# Text
FONT = "Garamond"
BASE_FONT_SIZE = DOC_HEIGHT*(1/72)
#  Title
MAX_TITLE_LEN = DOC_WIDTH/BASE_FONT_SIZE
TITLE_FONT_SIZE = BASE_FONT_SIZE*(3)
DEFAULT_TITLE = "Calendar of Weeks"
#  Legend
LEGEND_FONT_SIZE = BASE_FONT_SIZE*(1/2)
LEGEND_BIRTHDAY = "Birthday"
LEGEND_NEWYEAR = "New year"
#  Week label parallel to grid
WEEK_FONT_SIZE = BASE_FONT_SIZE*(1/2)
#  Year label parallel to grid
YEAR_FONT_SIZE = BASE_FONT_SIZE*(1/3)

# Colours
RGB_MAX = 255
WHITE = (RGB_MAX/RGB_MAX, RGB_MAX/RGB_MAX, RGB_MAX/RGB_MAX)
BLACK = (0/RGB_MAX, 0/RGB_MAX, 0/RGB_MAX)
BOX_LINE_COLOUR = BLACK
PAST_COLOUR = (51/RGB_MAX, 51/RGB_MAX, 51/RGB_MAX)
FUTURE_COLOUR = WHITE
BIRTHDAY_COLOUR = (196/RGB_MAX, 82/RGB_MAX, 92/RGB_MAX)
NEWYEAR_COLOUR = (239/RGB_MAX, 195/RGB_MAX, 166/RGB_MAX)
ENDYEAR_COLOUR = (196/RGB_MAX, 166/RGB_MAX, 239/RGB_MAX)
ISO_ENDYEAR_COLOUR = (255/RGB_MAX, 221/RGB_MAX, 0/RGB_MAX)


def parse_date(date):
    formats = ['%Y/%m/%d', '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']

    for f in formats:
        try:
            ret = datetime.datetime.strptime(date.strip(), f)
        except ValueError:
            continue
        else:
            return ret

    raise argparse.ArgumentTypeError("incorrect date format")

def parse_date(date):
    formats = ['%d/%m/%Y', '%d-%m-%Y']
    stripped = date.strip()

    for f in formats:
        try:
            ret = datetime.datetime.strptime(date, f)
        except:
            continue
        else:
            return ret

    raise ValueError("Incorrect date format: must be dd-mm-yyyy or dd/mm/yyyy")

def text_size(ctx, text):
    # calculates (essentially) the dimensions of a rectangle encompassing the text
    # returns a tuple corresponding to the wifth and height of that rectangle
    _, _, width, height, _, _ = ctx.text_extents(text)
    return width, height

def draw_diamond(ctx, pos_x, pos_y, fill):
    """
    Draws a diamond at pos_x,pos_y
    """
    ctx.set_line_width(BOX_LINE_WIDTH)
    ctx.set_source_rgb(*BOX_LINE_COLOUR)
    
    ctx.move_to(pos_x, pos_y + BASE_BOX_SIZE/2)
    ctx.line_to(pos_x + BASE_BOX_SIZE/2, pos_y)
    ctx.line_to(pos_x + BASE_BOX_SIZE, pos_y + BASE_BOX_SIZE/2)
    ctx.line_to(pos_x + BASE_BOX_SIZE/2, pos_y + BASE_BOX_SIZE)
    ctx.close_path ()
    ctx.stroke_preserve()

    ctx.set_source_rgb(*fill)
    ctx.fill()

def draw_square(ctx, pos_x, pos_y, fill):
    """
    Draws a square at pos_x,pos_y
    """
    ctx.set_line_width(BOX_LINE_WIDTH)
    ctx.set_source_rgb(*BOX_LINE_COLOUR)
    ctx.move_to(pos_x, pos_y)

    ctx.rectangle(pos_x, pos_y, BASE_BOX_SIZE, BASE_BOX_SIZE)
    ctx.stroke_preserve()

    ctx.set_source_rgb(*fill)
    ctx.fill()

def is_53_week_year(date):
    # ISO 8601
    # If January 1 is Monday—Thursday, 
    #       then January 1 is Week 1 of the current year
    # If January 1 is Friday, 
    #       then January 1 is Week 53 of the previous year
    # If January 1 is Saturday AND this was a leap year, 
    #       then January 1 is Week 53 of the previous year
    # If January 1 is Saturday AND this was not a leap year, 
    #       then January 1 is Week 52 of the previous year
    # If January 1 is Sunday
    #       then January 1 is Week 52 of the previous year
    ISO = False

    date = datetime.datetime(date.year, 12, 31)
    
    if ISO:
        return (int(date.strftime('%V')) == 53)
    else:
        return (int(date.strftime('%U')) == 53)

def is_current_week(now, month, day):
    end = now + datetime.timedelta(weeks=1)
    date1 = datetime.datetime(now.year, month, day)
    date2 = datetime.datetime(now.year + 1, month, day)

    return (now <= date1 < end) or (now <= date2 < end)

def calc_adjust(birthdate):
    """
    Calculates the week of the year in which the birthdate occurs (max and min)
    """
    max = 0
    min = 53
    for i in range(7):
        birth_week = (int(birthdate.strftime('%U'))) 
        if birth_week > max:
            max = birth_week
        if birth_week < min:
            min = birth_week
    
    return max, min

def is_leap_year(date):
    year = int(date.year)
    if (year%400 == 0):
        return True
    elif (year%100 == 0):
        return False
    elif (year%4 == 0):
        return True
    else:
        return False

def set_fill(date, birthdate):
    if PAST_DATE >= datetime.datetime(date.year, date.month, date.day):
        fill = PAST_COLOUR
    else:
        fill = FUTURE_COLOUR
    
    if is_current_week(date, birthdate.month, birthdate.day):
        fill = BIRTHDAY_COLOUR
    elif is_current_week(date, 1, 1):
        fill = NEWYEAR_COLOUR
    # elif is_current_week(date, 12, 31):
    #     fill = ENDYEAR_COLOUR
    # elif is_current_week(date, 12, 28):
    #     fill = ISO_ENDYEAR_COLOUR

    return fill 
    
def draw_row(ctx, pos_y, birthdate, date):
    """
    Draws a row of squares/diamonds starting at pos_y
    """
    pos_x = GRID_X_MARGIN
    adjust_max, adjust_min = calc_adjust(birthdate)
    pos_x_jan = 0
    pos_x_jan_max = 0

    for i in range(NUM_WEEKS):
        # if is_53_week_year(date):
        #     fill = (RGB_MAX/RGB_MAX, RGB_MAX/RGB_MAX, RGB_MAX/RGB_MAX)
        #     draw_square(ctx, pos_x, pos_y, fill)
        # if is_current_week(date, 12, 31):
        #     fill = ENDYEAR_COLOUR
        #     draw_square(ctx, pos_x, pos_y, fill)
        # if is_current_week(date, 12, 28):
        #     fill = ISO_ENDYEAR_COLOUR
        #     draw_square(ctx, pos_x, pos_y, fill)

        fill = set_fill(date, birthdate)
        #draw_square(ctx, pos_x, pos_y, fill)
        draw_diamond(ctx, pos_x, pos_y, fill)
        #draw_week_label()

        # Increment
        previous_date = date
        date += datetime.timedelta(days=7)
        pos_x += BASE_BOX_SIZE + GRID_SPACING
        
        # If the next box would be the birthday week, move to the next row
        if is_current_week(date, birthdate.month, birthdate.day):
            break
        
        # If the next box would be the week of Jan 1, make sure it is aligned as Week 1
        if is_current_week(date, 1, 1):
            birth_date_current = datetime.datetime(date.year, birthdate.month, birthdate.day)
            birth_weekday = (int(birth_date_current.strftime('%w')))
            birth_week = (int(birth_date_current.strftime('%U')))
            birth_day = (int(birth_date_current.strftime('%j')))
            
            last_day = datetime.datetime(previous_date.year, 12, 31)
            last_weekday = (int(last_day.strftime('%w')))
            last_week = (int(last_day.strftime('%U')))
            last_day = (int(last_day.strftime('%j')))

            # To align Week 1, sometimes we need to skip a box-space  
            # Why? Years have different lengths (365, 366) and weekdays shift.
            # As such, birthdays occur in two different weeks
            # # If the birthday is in its earlier week
            # # If Dec 31 is Wednesday, 
            # #       then January 1 is Week 1 of the current year
            # # If Dec 31 is Monday AND this was a leap year, 
            # #       then January 1 is Week 53 of the previous year
            debug_string = "{}: weekday:{} last_week:{}"
            debug_string = debug_string.format(date.year, int((birth_weekday+last_weekday)%7), last_week)
            print(debug_string)
            
            if birth_week == adjust_min:
                debug_string = "{}: X:{}: day:{} weekday:{} last_week:{}"
                debug_string = debug_string.format(date.year, int(pos_x), int(last_day-birth_day), int((birth_weekday+last_weekday)%7), last_week)

                pos_x += BASE_BOX_SIZE + GRID_SPACING
                if last_weekday == 3:
                    pos_x -= BASE_BOX_SIZE + GRID_SPACING
                    #print(debug_string)
                elif (last_weekday == 1) and (is_leap_year(date)):
                    pos_x -= BASE_BOX_SIZE + GRID_SPACING
                    #print(debug_string)
                
                pos_x_jan = int(pos_x)
                if pos_x_jan > pos_x_jan_max:
                    pos_x_jan_max = pos_x_jan

                #debug_string = "{}: X: {}: {} Dec 31 {}; F: {}"
                #debug_string = debug_string.format(date.year, int(pos_x), last_weekday, last_day, last_week )
    
    return date

def draw_column(ctx, pos_x, birthdate, date):
    """
    Draws a column of squares/diamonds starting at pos_x
    """
    pos_y = GRID_Y_MARGIN

    for i in range(NUM_WEEKS):
        fill = set_fill(date, birthdate)
        
        #draw_square(ctx, pos_x, pos_y, fill)
        draw_diamond(ctx, pos_x, pos_y, fill)
        pos_y += BASE_BOX_SIZE + GRID_SPACING
        date += datetime.timedelta(weeks=1)

def draw_grid(ctx, date, birthdate, num_years):
    """
    Draws the whole grid of squares (NUM_WEEKS * num_years)
    """
    pos_y = GRID_Y_MARGIN
    pos_x = GRID_X_MARGIN

    if(LANDSCAPE):
        for i in range(num_years):
            draw_current_year_label(ctx, date, pos_x, pos_y)
            draw_column(ctx, pos_x, birthdate, date)
            # Increment x position and current date by 1 column
            pos_x += BASE_BOX_SIZE + GRID_SPACING
            date += datetime.timedelta(weeks=NUM_WEEKS) # Will need to change for Landscape
    else:    
        for i in range(num_years):
            draw_current_year_label(ctx, date, pos_x, pos_y)
            date = draw_row(ctx, pos_y, birthdate, date)
            # Increment y position and current date by 1 row
            pos_y += BASE_BOX_SIZE + GRID_SPACING
            #date += datetime.timedelta(weeks=NUM_WEEKS) # Will need to change for Landscape

def draw_legend(ctx, pos_x, pos_y):
    ctx.set_font_size(LEGEND_FONT_SIZE)
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    pos_x = draw_legend_entry(ctx, pos_x, pos_y, LEGEND_BIRTHDAY, BIRTHDAY_COLOUR)
    draw_legend_entry(ctx, pos_x, pos_y, LEGEND_NEWYEAR, NEWYEAR_COLOUR)

def draw_legend_entry(ctx, pos_x, pos_y, entry_text, fill):
    draw_diamond(ctx, pos_x, pos_y, fill)
    pos_x += BASE_BOX_SIZE + (BASE_BOX_SIZE / 2)
    ctx.set_source_rgb(0, 0, 0)
    w, h = text_size(ctx, entry_text)
    ctx.move_to(pos_x, pos_y + (BASE_BOX_SIZE / 2) + (h / 2))
    ctx.show_text(entry_text)
    
    return pos_x + w + (BASE_BOX_SIZE * 2)

def draw_current_year_label(ctx, date, pos_x, pos_y):
    ctx.set_font_size(YEAR_FONT_SIZE)
    ctx.select_font_face(FONT, cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_source_rgb(0, 0, 0)

    # Define label 
    #date_str = date.strftime('%d %b, %Y')
    #date_str = date.strftime('%Y')
    year = int(date.strftime('%Y'))
    txt = "{} – {}"
    date_str = txt.format(year, year+1)

    w, h = text_size(ctx, date_str)
    # Draw it in front of the current row
    ctx.move_to(pos_x - w - BASE_BOX_SIZE, pos_y + ((BASE_BOX_SIZE / 2) + (h / 2)))
    ctx.show_text(date_str)

def draw_week_labels(ctx):
    ctx.set_font_size(WEEK_FONT_SIZE)
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL)

    pos_x = GRID_X_MARGIN
    pos_y = GRID_Y_MARGIN
    if(LANDSCAPE):
        for i in range(NUM_WEEKS):
            text = str(i + 1)
            w, h = text_size(ctx, text)
            ctx.move_to(pos_x - BASE_BOX_SIZE, pos_y + (BASE_BOX_SIZE / 2) + (h / 2))
            ctx.show_text(text)
            pos_y += BASE_BOX_SIZE + GRID_SPACING
    else:
        for i in range(NUM_WEEKS):
            text = str(i + 1)
            w, h = text_size(ctx, text)
            ctx.move_to(pos_x + (BASE_BOX_SIZE / 2) - (w / 2), pos_y - BASE_BOX_SIZE)
            ctx.show_text(text)
            pos_x += BASE_BOX_SIZE + GRID_SPACING

def draw_title(ctx, title):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_source_rgb(0, 0, 0)
    ctx.set_font_size(TITLE_FONT_SIZE)
    w, h = text_size(ctx, title)
    ctx.move_to((DOC_WIDTH / 2) - (w / 2), (GRID_Y_MARGIN / 2) - (h / 2))
    ctx.show_text(title)

def gen_calendar(birthdate, title, num_years, filename):
    # Init PDF 
    surface = cairo.PDFSurface (filename, DOC_WIDTH, DOC_HEIGHT)
    ctx = cairo.Context(surface)

    # Fill background with white
    ctx.set_source_rgb(1, 1, 1)
    ctx.rectangle(0, 0, DOC_WIDTH, DOC_HEIGHT)
    ctx.fill()

    # Define size of boxes
    #  Based on PDF dimensions and margins
    # This is currently done above, but Landscape may change this

    # Draw Title
    draw_title(ctx, title)

    # Draw Legend
    #  Puts legend part-way between top-left edge and grif
    LEGEND_X = GRID_X_MARGIN / 4
    LEGEND_Y = GRID_Y_MARGIN / 4
    #draw_legend(ctx, LEGEND_X, LEGEND_Y)
    
    # Draw week labels above grid
    #draw_week_labels(ctx)

    # Set Date
    date = birthdate
    #  Start each week on a specific weekday
    # 0 = Monday
    # 6 = Sunday
    while date.weekday() != 0:
        date -= datetime.timedelta(days=1)

    # Draw grid of NUM_YEARS x NUM_WEEKS 
    draw_grid(ctx, date, birthdate, num_years)
    ctx.show_page()

def main():
    parser = argparse.ArgumentParser(description='\nGenerate a personalized "Life '
        ' Calendar", inspired by the calendar with the same name from the '
        'waitbutwhy.com store')
    
    # birthdate (required)
    parser.add_argument(type=parse_date, dest='date', help='starting date; your birthday,'
        'in either yyyy/mm/dd or dd/mm/yyyy format (dashes \'-\' may also be used in '
        'place of slashes \'/\')')
    
    # filename (optional)
    parser.add_argument('-f', '--filename', type=str, dest='filename',
        help='output filename', default=DOC_NAME)
    
    # title (optional)
    parser.add_argument('-t', '--title', type=str, dest='title',
        help='Calendar title text (default is "%s")' % DEFAULT_TITLE,
        default=DEFAULT_TITLE)
    
    # age (optional; default 90): defines the maximum age, i.e. number of rows 
    parser.add_argument('-a', '--age', type=int, dest='age', choices=range(MIN_AGE, MAX_AGE + 1),
                        metavar='[%s-%s]' % (MIN_AGE, MAX_AGE),
                        help=('Number of rows to generate, representing years of life'),
                        default=DEFAULT_AGE)

    args = parser.parse_args()

    doc_name = '%s.pdf' % (os.path.splitext(args.filename)[0])

    try:
        if len(args.title) > MAX_TITLE_LEN:
            raise ValueError("Title can't be longer than %d characters" % MAX_TITLE_LEN)
        
        age = int(args.age)
        if (age < MIN_AGE) or (age > MAX_AGE):
            raise ValueError("Invalid age, must be between %d and %d" % (MIN_AGE, MAX_AGE))
        
        gen_calendar(args.date, args.title, age, doc_name)
    
    except Exception as e:
        print("Error: %s" % e)
        return
    
    print('Created %s' % doc_name)

if __name__ == "__main__":
    main()
