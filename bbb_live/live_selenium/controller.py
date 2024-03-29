import argparse
import logging
import os
import shlex
import signal
import subprocess

from bigbluebutton_api_python import BigBlueButton

from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait


logger = logging.getLogger("streamer")


class Streamer:
    def stream(self, bbb_join_url, display, stream_address, hide_presentation):
        for i in range(3):
            p = subprocess.run(f'pulseaudio --check', shell=True)
            if p.returncode != 0:
                logger.error("Pulseaudio hasn't started yet. Starting it")
                subprocess.run("pulseaudio --kill", shell=True)
                subprocess.run("pulseaudio -D", shell=True)
            else:
                logger.info("Pulseaudio is already running.")
                break

        options = ChromeOptions()
        options.add_argument("--kiosk")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        options.add_argument("--disable-infobars")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--window-position=0,0")
        options.add_argument("--start-fullscreen")

        logger.info("Started selenium controller browser")
        self.driver = webdriver.Chrome(options=options)

        self.driver.get(bbb_join_url)

        wait = WebDriverWait(self.driver, 60)
        wait.until(expected_conditions.visibility_of_element_located((By.XPATH, "//button[@aria-label='Play audio']")))

        self.driver.find_element_by_xpath("//button[@aria-label='Play audio']").click()

        # Remove fullscreen buttons
        x = self.driver.find_element_by_xpath("//button[@aria-label='Make Presentation fullscreen']")
        class_name = x.get_attribute("class").split(" ")[-1]
        remove_fullscreen = f'x=document.createElement("style");x.innerText=".{class_name} {{display: none;}}";' \
                            'document.body.appendChild(x);'
        self.driver.execute_script(remove_fullscreen)

        # Remove header
        self.driver.execute_script('document.querySelector(\'header\').style.display = "none";')

        # Remove notifications
        remove_toastify = 'x=document.createElement("style");x.innerText=".Toastify {display: '\
                          'none;}";document.body.appendChild(x);'
        self.driver.execute_script(remove_toastify)

        # Remove hide presentation button
        x = self.driver.find_element_by_xpath("//button[@aria-label='Minimize presentation']")
        if hide_presentation:
            x.click()
        else:
            self.driver.execute_script(f'document.getElementById("{x.get_attribute("id")}").style.display = "none";')

        # Remove actions bar
        self.driver.execute_script('document.querySelector(\'[aria-label="Actions bar"]\').style.display="none";')

        logger.info("Start ffmpeg")
        #cmd = f'ffmpeg -thread_queue_size 1024 -framerate 30 -f x11grab -draw_mouse 0 -s 1920x1080 -i :{display} -thread_queue_size 1024 -f pulse -i default -ac 1 -c:a aac -b:a 160k -ar 44100 -threads 0 -c:v libx264 -profile:v baseline -pix_fmt yuv420p -f flv "{stream_address}"'
        cmd = f'ffmpeg -thread_queue_size 1024 -f x11grab -draw_mouse 0 -s 1920x1080 -i :{display} -thread_queue_size 1024 -f pulse -i default -ac 2 -c:a aac -b:a 160k -ar 44100 -threads 0 -c:v libx264 -x264-params "nal-hrd=cbr" -profile:v high -level:v 4.2 -vf format=yuv420p -b:v "3500k" -maxrate "3500k" -minrate "1750k" -bufsize "7000k" -g 60 -preset ultrafast -f flv "{stream_address}"'
        cmd = shlex.split(cmd)
        self.process = subprocess.Popen(cmd)
        self.process.communicate()

    def start_browser(self, meeting_id, password, stream_address, bbb_url, bbb_secret, hide_presentation):
        b = BigBlueButton(bbb_url, bbb_secret)
        params = {
            "userdata-bbb_auto_join_audio": "true",
            "userdata-bbb_force_listen_only": "true",
            "userdata-bbb_skip_check_audio": "true",
            "userdata-bbb_show_participants_on_login": "false",
            "userdata-bbb_show_public_chat_on_login": "false",
        }
        uri = b.get_join_meeting_url("Stream", meeting_id, password=password, params=params)
        from pyvirtualdisplay import Display
        with Display(size=(1920, 1080), color_depth=24) as disp:
            logger.info("Started virtual display")
            self.stream(uri, disp.display, stream_address, hide_presentation)

    def stop(self):
        os.system(f"kill -9 {self.process.pid}")
        self.driver.close()


def handle_sigterm(_signo, _stack_frame):
    streamer.stop()
    exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--meeting-id", help="ID of BBB Meeting", required=True)
    parser.add_argument("--meeting-password", help="Password of BBB Meeting", required=True)
    parser.add_argument("--stream-address", help="Address of the stream", required=True)
    parser.add_argument("--bbb-url", help="BBB url", required=True)
    parser.add_argument("--bbb-secret", help="BBB shared secret", required=True)
    parser.add_argument("--hide-presentation", action="store_true", help="Specify True to hide the presentation")
    args = parser.parse_args()
    streamer = Streamer()

    signal.signal(signal.SIGTERM, handle_sigterm)
    streamer.start_browser(
        args.meeting_id, args.meeting_password, args.stream_address, args.bbb_url, args.bbb_secret,
        args.hide_presentation
    )
