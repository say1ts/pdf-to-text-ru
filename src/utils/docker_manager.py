import subprocess
import logging
from contextlib import contextmanager
import time
from typing import Generator


class DockerContainerManager:
    def __init__(self, container_name: str, run_command: list[str], logger: logging.LoggerAdapter):
        self.container_name = container_name
        self.run_command = run_command
        self.logger = logger
        self.already_run = False

    def _container_exists(self) -> bool:
        try:
            subprocess.check_output(["docker", "inspect", self.container_name])
            return True
        except subprocess.CalledProcessError:
            return False

    def _container_is_running(self) -> bool:
        status = (
            subprocess.check_output(["docker", "ps", "-f", f"name={self.container_name}", "-q"])
            .decode()
            .strip()
        )
        return bool(status)

    def start(self) -> None:
        if not self._container_exists():
            self.logger.info(f"Creating and starting container {self.container_name}")
            subprocess.run(self.run_command, check=True)
            self.logger.info("Awaiting for init container")
            # Могут быть ошибки, если долго грузится образ !! Нужно поставить await на скачивание образа
            time.sleep(1)
            self.logger.critical("You need to set bigger await span for download docker image!")
        elif not self._container_is_running():
            self.logger.info(f"Starting existing container {self.container_name}")
            subprocess.run(["docker", "start", self.container_name], check=True)

            awaiting_time = 10
            self.logger.info(f"Awaiting {awaiting_time} seconds for relaunch container")
            time.sleep(awaiting_time)
        else:
            # TODO прописать конкретное условие проверки запущенного контейнера
            self.already_run = True
            self.logger.info(f"Container {self.container_name} already running")

    def stop(self) -> None:
        if self.already_run:
            self.logger.info(
                f"Container is not stopped {self.container_name}, becouse was already started at the start of the program"
            )
            self.logger.warning("Be careful, VRAM probably MAY RUN OUT")
            return
        if self._container_is_running():
            self.logger.info(f"Stopping container {self.container_name}")
            subprocess.run(["docker", "stop", self.container_name], check=True)
            self.logger.info("Waiting 5 seconds for docker shutdown")
            time.sleep(5)
        else:
            self.logger.info(f"Container {self.container_name} not running")


@contextmanager
def managed_docker_container(
    container_name: str, run_command: list[str], logger: logging.LoggerAdapter
) -> Generator[None, None, None]:
    manager = DockerContainerManager(container_name, run_command, logger)
    manager.start()
    try:
        yield
    finally:
        manager.stop()
