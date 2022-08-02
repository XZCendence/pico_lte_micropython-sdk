"""
Module for communicating with cellular modem over UART interface.
"""

import time
from machine import UART, Pin
from core.temp import debug
from core.utils.status import Status


class MessageBuffer:
    """Buffer class for storing messages"""

    buffer = ""

    def add_message(self, message):
        self.buffer += message

    def any_data(self):
        return len(self.buffer)

    def get_message(self):
        return self.buffer

    def clear(self):
        self.buffer = ""

    def clear_before_id(self, id):
        self.buffer = self.buffer[id:]


class ATCom:
    """Class for handling AT communication with modem"""

    def __init__(
        self,
        uart_number = 0,
        tx_pin = Pin(0),
        rx_pin = Pin(1),
        baudrate = 115200,
        timeout = 10000
        ):
        self.buffer = MessageBuffer()
        self.modem_com = UART(
            uart_number,
            tx = tx_pin,
            rx = rx_pin,
            baudrate=baudrate,
            timeout=timeout
            )

    def send_at_comm_once(self, command, line_end=True):
        """
		Function for sending AT commmand to modem

		Parameters
        ----------
        command: str
            AT command to send
        line_end: bool
            if True, send line end

        """
        if line_end:
            compose = f"{command}\r".encode()
        else:
            compose = command.encode()
        debug.debug(compose)
        try:
            self.modem_com.write(compose)
        except:
            debug.error("Error occured while AT command writing to modem")

    def get_response(self, desired_responses="OK", timeout=5):
        """
		Function for getting modem response

        Parameters
        ----------
        desired_response: str
            desired response from modem
        timeout: int
            timeout for getting response

        Returns
        -------
        response: dict
            response from modem
		"""
        response = ""

        timer = time.time()
        while True:
            time.sleep(0.1) # wait for new chars

            if time.time() - timer < timeout:
                while self.modem_com.any():
                    try:
                        response += self.modem_com.read(self.modem_com.any()).decode('utf-8')
                    except:
                        pass
            else:
                return {"status": Status.TIMEOUT, "response": "timeout"}

            if isinstance(desired_responses, str):
                if desired_responses in response:
                    return {"status": Status.SUCCESS, "response": response}
                elif "ERROR" in response:
                    return {"status": Status.ERROR, "response": response}

            elif isinstance(desired_responses, list):
                for desired_response in desired_responses:
                    if desired_response in response:
                        return {"status": Status.SUCCESS, "response": response}
                    elif "ERROR" in response:
                        return {"status": Status.ERROR, "response": response}

    def send_at_comm(self, command, response="OK", timeout=5, line_end=True):
        """
		Function for writing AT command to modem and getting modem response

        Parameters
        ----------
        command: str
            AT command to send
        response: str
            desired response from modem
        timeout: int
            timeout for getting response

        Returns
        -------
        response: dict
            response from modem
		"""
        self.send_at_comm_once(command, line_end=line_end)
        time.sleep(0.1)
        return self.get_response(response, timeout)

    def retry_at_comm(self, command, response="OK", timeout=5, retry_count=3, interval=1):
        """
        Function for retrying AT command to modem and getting modem response

        Parameters
        ----------
        command: str
            AT command to send
        response: str
            desired response from modem
        timeout: int
            timeout for getting response
        retry_count: int
            number of retries
        interval: int
            interval between retries

        Returns
        -------
        response: dict
            response from modem
        """
        for _ in range(retry_count):
            result = self.send_at_comm(command, response, timeout)
            if result["status"] == Status.SUCCESS:
                return result
            else:
                time.sleep(interval)
        return result

    def listen_and_save_messages(self):
        """
        Function for listening modem messages and add them to buffer
        """
        len = self.modem_com.any()
        if len:
            message = self.modem_com.read(len).decode('utf-8')
            message = message.replace("\r", "\n") # replace carriage return with line end
            self.buffer.add_message(message)
         