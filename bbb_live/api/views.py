import json
import os
import signal
import subprocess
import sys

from django.http import JsonResponse
from django.views.generic.base import View
from rc_protocol import validate_checksum

from bbb_live import settings


class Process:
    @classmethod
    def start_stream(cls, data):
        cmd = f"{sys.executable} {os.path.join(settings.BASE_DIR, 'live_selenium', 'controller.py')} " \
              f"--bbb-url '{settings.BBB_URL}' --bbb-secret '{settings.BBB_SECRET}' " \
              f"--stream-address '{data['rtmp_uri']}' --meeting-id '{data['meeting_id']}' "\
              f"--meeting-password '{data['meeting_password']}'"
        cls.process = subprocess.Popen(cmd, shell=True)

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


class StartStream(View):

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "message": "Couldn't decode json"},
                status=400
            )
        check_result = check_required_parameter(["rtmp_uri", "meeting_id", "meeting_password", "checksum"], data)
        if not check_result["success"]:
            return JsonResponse(check_result, status=400)
        if not validate_checksum(data, settings.SHARED_SECRET, salt="startStream",
                                 time_delta=settings.SHARED_SECRET_TIME_DELTA):
            return JsonResponse(
                {"success": False, "message": "You didn't passed the checksum check"},
                status=401
            )
        if Process.is_running():
            return JsonResponse(
                {"success": False, "message": "There is already a meeting running on this server"},
                status=503
            )
        Process.start_stream(data)

        return JsonResponse({"success": True, "message": "Stream is starting."})


class StopStream(View):

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "message": "Couldn't decode json"},
                status=400
            )
        check_result = check_required_parameter(["meeting_id", "checksum"], data)
        if not check_result["success"]:
            return JsonResponse(check_result, status=400)
        if not validate_checksum(data, settings.SHARED_SECRET, "stopStream", settings.SHARED_SECRET_TIME_DELTA):
            return JsonResponse(
                {"success": False, "message": "You didn't passed the checksum check"},
                status=401
            )
        Process.stop_stream()

        return JsonResponse({"success": True, "message": "Stream was stopped."})
