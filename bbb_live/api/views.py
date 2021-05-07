import os
import shlex
import signal
import subprocess
import sys

from django.http import JsonResponse
from bbb_common_api.views import PostApiPoint

from bbb_live import settings


class Process:
    @classmethod
    def start_stream(cls, data):
        cmd = f"{sys.executable} {os.path.join(settings.BASE_DIR, 'live_selenium', 'controller.py')} " \
              f"--bbb-url '{settings.BBB_URL}' --bbb-secret '{settings.BBB_SECRET}' " \
              f"--stream-address '{data['rtmp_uri']}' --meeting-id '{data['meeting_id']}' "\
              f"--meeting-password '{data['meeting_password']}' "\
              f"{'--hide-presentation' if 'hide_presentation' in data else ''}"
        cmd = shlex.split(cmd)
        cls.process = subprocess.Popen(cmd)

    @classmethod
    def stop_stream(cls):
        cls.process.send_signal(signal.SIGTERM)
        del cls.process

    @classmethod
    def is_running(cls):
        return hasattr(cls, "process")


def check_required_parameter(param_list, data):
    missing_params = [x for x in param_list if x not in data]
    if len(missing_params) > 0:
        return {"success": False, "message": f'{", ".join(missing_params)} are missing, but required'}
    return {"success": True}


class StartStream(PostApiPoint):

    endpoint = "startStream"
    required_parameters = ["rtmp_uri", "meeting_id", "meeting_password"]

    def safe_post(self, request, parameters, *args, **kwargs):
        if Process.is_running():
            return JsonResponse(
                {"success": False, "message": "There is already a meeting running on this server"},
                status=503
            )
        Process.start_stream(parameters)

        return JsonResponse({"success": True, "message": "Stream is starting."})


class StopStream(PostApiPoint):

    endpoint = "stopStream"
    required_parameters = ["meeting_id"]

    def safe_post(self, request, parameters, *args, **kwargs):
        Process.stop_stream()

        return JsonResponse({"success": True, "message": "Stream was stopped."})
