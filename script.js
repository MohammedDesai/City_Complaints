/**
 * City Complaint Tracker - front-end helpers
 *
 * 1. "Use My Location" - captures browser GPS coordinates into hidden
 *    form fields on the complaint submission page.
 * 2. Tracking page auto-refresh - polls GET /api/track/<tracking_id>
 *    every 30 seconds and updates the DOM in place (no full page reload).
 */

(function () {
    const REFRESH_INTERVAL_MS = 30000; // 30 seconds

    document.addEventListener("DOMContentLoaded", function () {
        initGpsCapture();
        initTrackingAutoRefresh();
    });

    // -----------------------------------------------------------------
    // GPS capture (submission form)
    // -----------------------------------------------------------------
    function initGpsCapture() {
        const btn = document.getElementById("use-my-location-btn");
        if (!btn) {
            return; // Not on the submission page
        }

        const latField = document.getElementById("latitude");
        const lngField = document.getElementById("longitude");
        const statusEl = document.getElementById("gps-status");

        btn.addEventListener("click", function () {
            if (!("geolocation" in navigator)) {
                setGpsStatus(statusEl, "Geolocation is not supported by this browser.", false);
                return;
            }

            setGpsStatus(statusEl, "Requesting your location...", null);

            navigator.geolocation.getCurrentPosition(
                function (position) {
                    latField.value = position.coords.latitude;
                    lngField.value = position.coords.longitude;
                    setGpsStatus(
                        statusEl,
                        "Location captured (" +
                            position.coords.latitude.toFixed(5) +
                            ", " +
                            position.coords.longitude.toFixed(5) +
                            ").",
                        true
                    );
                },
                function (error) {
                    setGpsStatus(statusEl, "Could not get your location: " + error.message, false);
                },
                { enableHighAccuracy: true, timeout: 10000 }
            );
        });
    }

    function setGpsStatus(el, message, success) {
        if (!el) return;
        el.textContent = message;
        el.classList.remove("text-success", "text-danger");
        if (success === true) {
            el.classList.add("text-success");
        } else if (success === false) {
            el.classList.add("text-danger");
        }
    }

    // -----------------------------------------------------------------
    // Tracking page auto-refresh
    // -----------------------------------------------------------------
    function initTrackingAutoRefresh() {
        const resultBox = document.getElementById("complaint-result");
        if (!resultBox) {
            return; // No complaint currently displayed - nothing to poll
        }

        const trackingId = resultBox.getAttribute("data-tracking-id");
        if (!trackingId) {
            return;
        }

        setInterval(function () {
            refreshComplaintStatus(trackingId);
        }, REFRESH_INTERVAL_MS);
    }

    function refreshComplaintStatus(trackingId) {
        const refreshErrorEl = document.getElementById("refresh-error");

        fetch(`/api/track/${encodeURIComponent(trackingId)}`)
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("Network response was not OK (" + response.status + ")");
                }
                return response.json();
            })
            .then(function (data) {
                if (!data.success) {
                    throw new Error(data.error || "Unknown error");
                }
                updateComplaintUI(data.complaint);
                if (refreshErrorEl) {
                    refreshErrorEl.classList.add("d-none");
                }
            })
            .catch(function (err) {
                console.error("Auto-refresh failed:", err);
                if (refreshErrorEl) {
                    refreshErrorEl.classList.remove("d-none");
                }
            });
    }

    function setBadge(el, text, classPrefix, value) {
        if (!el) return;
        el.textContent = text;
        el.className =
            "badge status-badge " + classPrefix + "-" + String(value).replace(/\s+/g, "-").toLowerCase();
    }

    function updateComplaintUI(complaint) {
        // Status badge
        setBadge(
            document.getElementById("status-badge"),
            complaint.status,
            "status",
            complaint.status
        );

        // Severity / priority / SLA badges
        setBadge(
            document.getElementById("severity-badge"),
            "Severity: " + complaint.severity,
            "severity",
            complaint.severity
        );
        setBadge(
            document.getElementById("priority-badge"),
            "Priority: " + complaint.priority_label,
            "priority",
            complaint.priority_label
        );
        setBadge(
            document.getElementById("sla-badge"),
            "SLA: " + complaint.sla_status,
            "sla",
            complaint.sla_status
        );

        // Timestamps
        const updatedAtEl = document.getElementById("updated-at");
        if (updatedAtEl) {
            updatedAtEl.textContent = complaint.updated_at;
        }
        const slaDueAtEl = document.getElementById("sla-due-at");
        if (slaDueAtEl && complaint.sla_due_at) {
            slaDueAtEl.textContent = complaint.sla_due_at;
        }

        // Other fields that could change over time
        const descriptionEl = document.getElementById("description-text");
        if (descriptionEl) {
            descriptionEl.textContent = complaint.description;
        }
        const locationEl = document.getElementById("location-text");
        if (locationEl) {
            locationEl.textContent = complaint.location;
        }

        // After photo (appears once the complaint is resolved with proof)
        const afterWrapper = document.getElementById("after-photo-wrapper");
        const afterImg = document.getElementById("after-photo-img");
        if (afterWrapper && afterImg && complaint.after_photo_filename) {
            afterImg.src = "/uploads/" + complaint.after_photo_filename;
            afterWrapper.style.display = "";
        }

        // Verification prompt - show once resolved and not yet verified
        const verifyPrompt = document.getElementById("verify-prompt");
        if (verifyPrompt) {
            const shouldShow =
                complaint.status === "Resolved" && complaint.verification_status !== "Verified Fixed";
            verifyPrompt.style.display = shouldShow ? "" : "none";
        }
    }
})();
