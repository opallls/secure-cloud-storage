ValueError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).
Traceback:
File "/mount/src/secure-cloud-storage/streamlit_app.py", line 286, in <module>
    service = get_drive_service()
File "/mount/src/secure-cloud-storage/google_drive.py", line 79, in get_drive_service
    creds = _load_creds_from_streamlit_secrets()
File "/mount/src/secure-cloud-storage/google_drive.py", line 43, in _load_creds_from_streamlit_secrets
    return Credentials.from_authorized_user_info(token_info, SCOPES)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.14/site-packages/google/oauth2/credentials.py", line 498, in from_authorized_user_info
    expiry = datetime.strptime(
        expiry.rstrip("Z").split(".")[0], "%Y-%m-%dT%H:%M:%S"
    )
File "/usr/local/lib/python3.14/_strptime.py", line 815, in _strptime_datetime_datetime
    tt, fraction, gmtoff_fraction = _strptime(data_string, format)
                                    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.14/_strptime.py", line 555, in _strptime
    raise ValueError("time data %r does not match format %r" %
                     (data_string, format))
