# BBB Live

This component manages the start and stop of a rtmp stream.

## API
The data of all POST requests have to be json encoded.

### Authentication

The authentication is done with [RCP](https://github.com/myOmikron/rcp). Use the name of the endpoint  as salt and include the
checksum as key "checksum". The checksum is required at every endpoint.

### startStream
- Method `POST`

This endpoint starts a stream for a given BBB Meeting to a target rtmp address.
As for now, only one stream can be running at the same time.

Parameter         | Optional | Type | Description
---               | ---      | ---  | ---
rtmp_uri          | No       | str  | RTMP Address of the target server
meeting_id        | No       | str  | BBB Meeting ID
meeting_password  | No       | str  | BBB Meeting Attendee or Moderator Password
hide_presentation | Yes      | bool | If specified True, the presentation will be hidden


### stopStream
- Method `POST`

This endpoint stops a stream for a given BBB Meeting.

Parameter  | Description
---        | ---
meeting_id | BBB Meeting ID
