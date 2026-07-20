from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from kivy.utils import platform


GrantedCallback = Callable[[], None]
DeniedCallback = Callable[[str], None]


class AndroidTrackingServiceController:
    """
    Управляет foreground service из UI-процесса.
    """

    SERVICE_CLASS_NAME = "ServiceTracking"

    def request_permissions(
        self,
        *,
        on_granted: GrantedCallback,
        on_denied: DeniedCallback,
    ) -> None:
        if platform != "android":
            on_granted()
            return

        try:
            from android.permissions import (
                Permission,
                check_permission,
                request_permissions,
            )

            coarse = Permission.ACCESS_COARSE_LOCATION
            fine = Permission.ACCESS_FINE_LOCATION

            if (
                check_permission(coarse)
                or check_permission(fine)
            ):
                self._request_notification_permission(
                    on_complete=on_granted,
                )
                return

            def location_callback(
                permissions: list[str],
                results: list[bool],
            ) -> None:
                permission_results = dict(
                    zip(permissions, results)
                )

                has_location = bool(
                    permission_results.get(coarse, False)
                    or permission_results.get(fine, False)
                    or check_permission(coarse)
                    or check_permission(fine)
                )

                if not has_location:
                    on_denied(
                        "Для записи маршрута необходимо "
                        "разрешить доступ к геолокации"
                    )
                    return

                self._request_notification_permission(
                    on_complete=on_granted,
                )

            request_permissions(
                [
                    coarse,
                    fine,
                ],
                location_callback,
            )

        except Exception as error:
            on_denied(
                f"Ошибка запроса Android-разрешений: {error}"
            )

    def _request_notification_permission(
        self,
        *,
        on_complete: GrantedCallback,
    ) -> None:
        try:
            from android.permissions import (
                check_permission,
                request_permissions,
            )
            from jnius import autoclass

            android_version = autoclass(
                "android.os.Build$VERSION"
            )

            if int(android_version.SDK_INT) < 33:
                on_complete()
                return

            permission = (
                "android.permission.POST_NOTIFICATIONS"
            )

            if check_permission(permission):
                on_complete()
                return

            request_permissions(
                [permission],
                lambda *_args: on_complete(),
            )

        except Exception:
            on_complete()

    def start(
        self,
        *,
        run_id: int,
        database_path: Path | str,
        state_path: Path | str,
        min_time: int = 1000,
        min_distance: float = 1.0,
    ) -> None:
        if platform != "android":
            raise RuntimeError(
                "Foreground service доступен только на Android"
            )

        from jnius import autoclass

        activity = autoclass(
            "org.kivy.android.PythonActivity"
        ).mActivity

        package_name = activity.getPackageName()

        service_class = autoclass(
            f"{package_name}.{self.SERVICE_CLASS_NAME}"
        )

        argument = json.dumps(
            {
                "run_id": int(run_id),
                "database_path": str(database_path),
                "state_path": str(state_path),
                "min_time": int(min_time),
                "min_distance": float(min_distance),
            },
            ensure_ascii=False,
        )

        service_class.start(
            activity,
            argument,
        )

    def stop(self) -> None:
        if platform != "android":
            return

        from jnius import autoclass

        activity = autoclass(
            "org.kivy.android.PythonActivity"
        ).mActivity

        package_name = activity.getPackageName()

        service_class = autoclass(
            f"{package_name}.{self.SERVICE_CLASS_NAME}"
        )

        service_class.stop(activity)