import lib.display
import lib.server
import time
import gc

# init screen
screen = lib.display.landscape()

# init server
screen.writeToCenter("loading...")
server = lib.server
# server.startServer(screen) # testing fun html server
timeIsSet = server.syncTime(screen)

# some functions
def timeMins(time):
    h, m = map(int, time.split(":"))
    return h * 60 + m

def minsTime(mins):
    h = mins // 60
    m = mins % 60
    return f"{h}h {m}min" # f"{h:02}h {m:02}min"

# main
if not timeIsSet:
    time.sleep(1)
    screen.writeToCenter(["EXIT", "Couldn't sync time."])
else:
    screen.Clear()
    bg = 0xff
    fg = 0x00

    # main cycle
    while True:
        screen.fill(bg)
        
        scheduleWeekday = [
            {'start': "00:30", 'stop': "05:30"},
            {'start': "12:30", 'stop': "15:30"}
        ]
        
        scheduleSaturday = [
            {'start': "02:30", 'stop': "05:30"},
            {'start': "12:30", 'stop': "17:30"}
        ]
        
        scheduleSunday = [
            {'start': "04:00", 'stop': "07:00"},
            {'start': "13:00", 'stop': "18:00"}
        ]
        
        timeNow = time.localtime()
        minNow = timeNow[3] * 60 + timeNow[4]
        dayNum = timeNow[6]

        if dayNum == 5:
            scheduleToday = scheduleSaturday
            schedulePrev = scheduleWeekday
            scheduleNext = scheduleSunday
        elif dayNum == 6:
            scheduleToday = scheduleSunday
            schedulePrev = scheduleSaturday
            scheduleNext = scheduleWeekday
        else:
            scheduleToday = scheduleWeekday
            schedulePrev = scheduleWeekday
            scheduleNext = scheduleWeekday

        # screen positioning
        startY = 0
        ratio = screen.height / (24 * 60) # ratio num min / day TO screen width (height and width are switched on landscape)
        rectHeight = int(screen.width / 3 * 2) + startY
        minOffset = minNow - (screen.height // 2) / ratio
        
        # paint blocks for day-1, today, day+1
        schedules = [schedulePrev, scheduleToday, scheduleNext]
        for i, schedule in enumerate(schedules):
            dayOffset = (i - 1) * (24 * 60)
            for entry in schedule:
                startX = int((timeMins(entry['start']) + dayOffset - minOffset) * ratio)
                stopX = int((timeMins(entry['stop']) + dayOffset - minOffset) * ratio)
                screen.fill_rect(startX, startY, stopX - startX, rectHeight, fg)

        # paint top border with timeline
        screen.fill_rect(0, 0, screen.height, 30, fg)
        
        period = 3
        hours = list(range(-24, 49, period))  # cover day-1, today, day+1 (24+24+24 +1 hr)
        tickWidth = int(screen.height / 24 * period)
        timelineOffset = ((minNow % (period * 60)) / (period * 60)) * tickWidth
        xPos = int((-screen.height * 1.5) + ((minOffset) * ratio) - timelineOffset - 12) # -12 aprox size of %NN
        for hour in hours:
            screen.text(f"{(hour % 24):02}", xPos, 14, bg)
            xPos += tickWidth

        # paint bottom border with countdown
        screen.fill_rect(0, screen.width - 22, screen.height, screen.width, fg)
        
        if minNow > timeMins(scheduleToday[-1]['stop']): # when this day period is over
            scheduleToday = scheduleNext  # pick tomorrow's schedule
        
        nextPeriod = timeMins(scheduleToday[0]['start']) # pick next schedule default
        periodAction = 'STARTS' # default action

        for entry in scheduleToday:
            start = timeMins(entry['start'])
            stop = timeMins(entry['stop'])
            if minNow < start:
                nextPeriod = start
                break
            if minNow < stop:
                nextPeriod = stop
                periodAction = 'STOPS'
                break

        countdown = nextPeriod - minNow
        if countdown < 0:
            countdown += 24 * 60
        countdown = f"BOJLER {periodAction} IN {minsTime(countdown)}"
        textWidth = len(countdown) * 8
        screen.text(countdown, (screen.height - textWidth) // 2, screen.width - 14, bg)
                
        # paint current cursor (static center)
        cursorX = screen.height // 2
        for i in range(8):
            screen.fill_rect(cursorX - (i + 1), startY + (6 + i * 2) + rectHeight, (2 + i * 2), 2, fg)

        # paint it all
        screen.display_fast(screen.buffer)

        gc.collect()
        time.sleep(1 * 60)
