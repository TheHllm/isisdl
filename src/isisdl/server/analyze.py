#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from distutils.version import Version
from typing import List, Union, Dict, Any, Optional, Set, DefaultDict

import matplotlib.pyplot as plt
from distlib.version import LegacyVersion

from isisdl.server.server_settings import server_path, log_dir_location, log_type, log_dir_version, graph_dir_location


# TODO:
#   Users over time → moving average window / first time registered.
#   Different OS versions


@dataclass
class DataV1:
    username: str
    OS: str
    OS_spec: str
    version: Union[LegacyVersion, Version]

    time: datetime
    is_first_time: bool
    num_g_files: int
    num_c_files: int
    total_g_bytes: int
    total_c_bytes: int
    course_ids: List[int]
    config: Dict[str, Union[bool, str, int, None, Dict[int, str]]]
    message: Optional[str] = None
    is_static: Optional[bool] = None
    current_database_version: Optional[int] = None
    database_version: Optional[int] = None
    has_ffmpeg: Optional[bool] = None
    forbidden_chars: Optional[List[int]] = None
    fstype: Optional[str] = None

    @classmethod
    def from_json(cls, info: Dict[str, Any]) -> DataV1:
        obj = cls(**info)
        the_time: int = obj.time  # type: ignore
        obj.time = datetime.fromtimestamp(the_time)

        return obj


def get_data() -> List[DataV1]:
    content: List[DataV1] = []
    for date in server_path.joinpath(log_dir_location, log_dir_version, log_type).glob("*"):
        for file in date.glob("*"):
            with file.open() as f:
                content.append(DataV1.from_json(json.load(f)))

    return content


def analyze_versions() -> None:
    data = get_data()
    users: DefaultDict[str, List[Union[LegacyVersion, Version]]] = defaultdict(list)

    for dat in data:
        users[dat.username].append(dat.version)

    versions: Dict[str, Union[LegacyVersion, Version]] = {}
    for user, _version in users.items():
        versions[user] = max(_version)

    perc_versions = []
    labels = []
    for version in set(versions.values()):
        perc_versions.append(list(versions.values()).count(version))
        labels.append(str(version))

    plt.title("Distribution of versions for isisdl")
    plt.pie(perc_versions, labels=labels)
    plt.tight_layout()
    plt.savefig(server_path.joinpath(log_dir_location, log_dir_version, graph_dir_location, "versions.png"))


def analyze_users_per_day() -> None:
    data = get_data()
    users: DefaultDict[str, int] = defaultdict(int)
    counted: Set[str] = set()

    for dat in data:
        if dat.time.strftime("%y-%m-%d ") + dat.username in counted:
            continue

        counted.add(dat.time.strftime("%y-%m-%d ") + dat.username)
        users[dat.time.strftime("%y-%m-%d")] += 1

    plt.title("Users over time for isisdl")
    plt.figure(dpi=300)
    plt.xticks(rotation=90)
    plt.plot(list(users.keys()), list(users.values()))
    plt.tight_layout()
    plt.show()
    plt.savefig(server_path.joinpath(log_dir_location, log_dir_version, graph_dir_location, "users_per_day.png"))


def analyze_new_users_over_time() -> None:
    data = get_data()

    users: DefaultDict[str, int] = defaultdict(int)
    counted: Set[str] = set()

    for dat in data:
        if dat.username in counted:
            continue

        counted.add(dat.username)
        users[dat.time.strftime("%y-%m-%d")] += 1

    # keys = set(users.keys())
    # for key in users.keys():
    #     i = 0

    print()
    pass


def remove_bad_files() -> None:
    for file in server_path.joinpath(log_dir_location, log_dir_version).rglob("*"):
        try:
            data = json.loads(file.read_text())
            if "config" not in data or data["username"] is None:
                file.unlink()

        except Exception:
            pass


def main() -> None:
    remove_bad_files()
    analyze_new_users_over_time()

    analyze_versions()
    analyze_users_per_day()
    return


if __name__ == '__main__':
    main()
