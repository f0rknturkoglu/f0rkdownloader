"""
Tests for Localhost Bridge Server and Queue.
"""

import json
import unittest
import urllib.request
from src.utils.bridge import BridgeQueue, LocalBridgeServer


class TestBridge(unittest.TestCase):
    """Unit tests for browser bridge and queue."""

    def test_bridge_queue_operations(self):
        queue = BridgeQueue()
        self.assertEqual(queue.total_count, 0)

        received_events = []
        queue.subscribe(lambda ev: received_events.append(ev))

        added = queue.add_batch("youtube", ["https://youtube.com/watch?v=1", "https://youtube.com/watch?v=2"])
        self.assertEqual(added, 2)
        self.assertEqual(queue.total_count, 2)
        self.assertEqual(len(received_events), 1)

        pending = queue.get_all_pending()
        self.assertEqual(len(pending), 1)
        self.assertEqual(len(pending[0]["urls"]), 2)
        self.assertEqual(queue.total_count, 0)

    def test_bridge_server_endpoints(self):
        server = LocalBridgeServer(host="127.0.0.1", port=48199)
        started = server.start()
        self.assertTrue(started)
        self.assertTrue(server.is_running)

        try:
            # 1. Test GET /api/status
            req = urllib.request.Request("http://127.0.0.1:48199/api/status")
            with urllib.request.urlopen(req, timeout=3) as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(data["status"], "online")
                self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")

            # 2. Test POST /api/queue
            payload = json.dumps({
                "platform": "tiktok",
                "urls": ["https://www.tiktok.com/@video/video/7654321"]
            }).encode("utf-8")
            post_req = urllib.request.Request(
                "http://127.0.0.1:48199/api/queue",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(post_req, timeout=3) as post_resp:
                self.assertEqual(post_resp.status, 200)
                res_data = json.loads(post_resp.read().decode("utf-8"))
                self.assertTrue(res_data["success"])
                self.assertEqual(res_data["received"], 1)

        finally:
            server.stop()
            self.assertFalse(server.is_running)


if __name__ == "__main__":
    unittest.main()
