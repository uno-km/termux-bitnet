"""Zero-dependency, OpenAI-compatible local HTTP server for termux-bitnet."""

import json
import time
import uuid
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Optional

from termux_bitnet.engine import BitNetEngine
from termux_bitnet.config import BitNetConfig

ENGINE_LOCK = threading.Lock()


class OpenAIHandler(BaseHTTPRequestHandler):
    engine: Optional[BitNetEngine] = None

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_GET(self):
        if self.path == "/health":
            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "healthy", "service": "termux-bitnet"}).encode("utf-8"))
        elif self.path in ("/v1/models", "/models"):
            self._set_headers(200)
            data = {
                "object": "list",
                "data": [
                    {
                        "id": "bitnet-b1.58-2b-4t",
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": "uno-km",
                    }
                ]
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10 MB Payload Guard

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
        except (ValueError, TypeError):
            self._send_json_error(400, "[termux-bitnet ERROR] Invalid Content-Length header.", "invalid_request_error")
            return

        if content_length > self.MAX_REQUEST_SIZE:
            self._send_json_error(413, f"[termux-bitnet ERROR] Payload Too Large. Maximum allowed size is {self.MAX_REQUEST_SIZE} bytes.", "payload_too_large")
            return

        if content_length < 0:
            self._send_json_error(400, "[termux-bitnet ERROR] Content-Length cannot be negative.", "invalid_request_error")
            return

        body = self.rfile.read(content_length)

        try:
            req_data = json.loads(body.decode("utf-8"))
        except Exception:
            self._send_json_error(400, "[termux-bitnet ERROR] Invalid JSON body", "invalid_request_error")
            return

        if self.path in ("/v1/chat/completions", "/chat/completions"):
            self._handle_chat_completions(req_data)
        elif self.path in ("/v1/completions", "/completions"):
            self._handle_completions(req_data)
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint Not Found"}).encode("utf-8"))

    def _send_json_error(self, status_code: int, message: str, error_type: str = "invalid_request_error"):
        self._set_headers(status_code)
        err_payload = {
            "error": {
                "message": message,
                "type": error_type,
                "code": status_code,
            }
        }
        self.wfile.write(json.dumps(err_payload).encode("utf-8"))

    def _handle_chat_completions(self, data):
        if not OpenAIHandler.engine:
            self._send_json_error(
                503,
                "[termux-bitnet ERROR] BitNet engine is not initialized.\n"
                "Please start the server with a valid model: termux-bitnet serve -m <model_path>\n"
                "Or download a model: termux-bitnet download bitnet-2b",
                "service_unavailable"
            )
            return

        messages = data.get("messages", [])
        if not messages or not isinstance(messages, list):
            self._send_json_error(
                400,
                "[termux-bitnet ERROR] 'messages' field is required and must be a non-empty array of message objects.",
                "invalid_request_error"
            )
            return

        stream = data.get("stream", False)
        max_tokens = data.get("max_tokens", 256)

        # Reconstruct full conversation prompt
        prompt_lines = []
        has_content = False
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if content and str(content).strip():
                has_content = True
            prompt_lines.append(f"{role.capitalize()}: {content}")
        prompt_lines.append("Assistant: ")
        prompt = "\n".join(prompt_lines)

        if not has_content:
            self._send_json_error(
                400,
                "[termux-bitnet ERROR] Messages cannot be all empty. Please provide valid message text.",
                "invalid_request_error"
            )
            return

        req_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created = int(time.time())

        if stream:
            headers_sent = False
            try:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                headers_sent = True

                import queue

                token_queue = queue.Queue(maxsize=32)
                cancel_event = threading.Event()
                worker_done = threading.Event()
                worker_err = []

                def _stream_producer():
                    try:
                        stream_gen = None
                        with ENGINE_LOCK:
                            stream_gen = OpenAIHandler.engine.generate_stream(prompt, max_tokens=max_tokens)

                        while not cancel_event.is_set():
                            chunk = None
                            with ENGINE_LOCK:
                                try:
                                    chunk = next(stream_gen)
                                except StopIteration:
                                    break
                                except Exception as ge:
                                    worker_err.append(ge)
                                    break

                            if chunk is not None:
                                while not cancel_event.is_set():
                                    try:
                                        token_queue.put(chunk, timeout=0.05)
                                        break
                                    except queue.Full:
                                        continue
                    except Exception as pe:
                        worker_err.append(pe)
                    finally:
                        worker_done.set()

                prod_thread = threading.Thread(target=_stream_producer, daemon=True)
                prod_thread.start()

                try:
                    while True:
                        try:
                            chunk = token_queue.get(timeout=0.05)
                            chunk_obj = {
                                "id": req_id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": "bitnet-b1.58-2b-4t",
                                "choices": [
                                    {"index": 0, "delta": {"content": chunk}, "finish_reason": None}
                                ]
                            }
                            self.wfile.write(f"data: {json.dumps(chunk_obj)}\n\n".encode("utf-8"))
                            self.wfile.flush()
                        except queue.Empty:
                            if worker_done.is_set() and token_queue.empty():
                                break
                            if worker_err:
                                raise worker_err[0]

                    done_obj = {
                        "id": req_id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": "bitnet-b1.58-2b-4t",
                        "choices": [
                            {"index": 0, "delta": {}, "finish_reason": "stop"}
                        ]
                    }
                    self.wfile.write(f"data: {json.dumps(done_obj)}\n\ndata: [DONE]\n\n".encode("utf-8"))
                    self.wfile.flush()
                finally:
                    cancel_event.set() # Stop producer thread and release ENGINE_LOCK deterministically
            except (BrokenPipeError, ConnectionResetError) as _client_disc:
                # Client disconnected prematurely
                import logging
                logging.getLogger("termux_bitnet.server").debug(
                    "[server] Client disconnected during streaming: %s", _client_disc
                )
            except Exception as e:
                if not headers_sent:
                    self._send_json_error(500, f"[termux-bitnet ERROR] Inference execution failed: {e}", "internal_error")
                else:
                    try:
                        err_chunk = {"error": {"message": str(e), "type": "internal_error", "code": 500}}
                        self.wfile.write(f"data: {json.dumps(err_chunk)}\n\n".encode("utf-8"))
                        self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError, OSError) as _flush_err:
                        # 클라이언트가 이미 연결 해제 — 오류 chunk 전송 불가.
                        # 메인 오류(e)는 이미 로깅된 상태이므로 연결 실패만 debug 기록.
                        import logging
                        logging.getLogger("termux_bitnet.server").debug(
                            "[server] Cannot flush error chunk to client (disconnected): %s", _flush_err
                        )

        else:
            try:
                with ENGINE_LOCK:
                    full_response = OpenAIHandler.engine.generate(prompt, max_tokens=max_tokens)
                self._set_headers(200)
                
                # Accurate token metrics via engine.count_tokens
                p_tokens = max(OpenAIHandler.engine.count_tokens(prompt), 1)
                c_tokens = max(OpenAIHandler.engine.count_tokens(full_response), 1)

                resp_obj = {
                    "id": req_id,
                    "object": "chat.completion",
                    "created": created,
                    "model": "bitnet-b1.58-2b-4t",
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": full_response},
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": p_tokens,
                        "completion_tokens": c_tokens,
                        "total_tokens": p_tokens + c_tokens
                    }
                }
                self.wfile.write(json.dumps(resp_obj).encode("utf-8"))
            except Exception as e:
                self._send_json_error(500, f"[termux-bitnet ERROR] Inference execution failed: {e}", "internal_error")

    def _handle_completions(self, data):
        if not OpenAIHandler.engine:
            self._send_json_error(
                503,
                "[termux-bitnet ERROR] BitNet engine is not initialized.\n"
                "Please start the server with a valid model: termux-bitnet serve -m <model_path>",
                "service_unavailable"
            )
            return

        prompt = data.get("prompt", "")
        if not prompt or not str(prompt).strip():
            self._send_json_error(
                400,
                "[termux-bitnet ERROR] 'prompt' field cannot be empty. Please provide valid text input.",
                "invalid_request_error"
            )
            return

        max_tokens = data.get("max_tokens", 256)
        try:
            with ENGINE_LOCK:
                full_response = OpenAIHandler.engine.generate(prompt, max_tokens=max_tokens)
            resp_obj = {
                "id": f"cmpl-{uuid.uuid4().hex[:12]}",
                "object": "text_completion",
                "created": int(time.time()),
                "model": "bitnet-b1.58-2b-4t",
                "choices": [{"text": full_response, "index": 0, "finish_reason": "stop"}]
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(resp_obj).encode("utf-8"))
        except Exception as e:
            self._send_json_error(500, f"[termux-bitnet ERROR] Inference execution failed: {e}", "internal_error")


def run_server(host: str = "0.0.0.0", port: int = 8080, model_path: str = ""):
    """Start standalone OpenAI-compatible local API server with multi-threaded request support."""
    config = BitNetConfig(model_path=model_path)
    engine = BitNetEngine(config)
    OpenAIHandler.engine = engine

    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, OpenAIHandler)

    print("=========================================================")
    print(f"  termux-bitnet OpenAI API Server running on {host}:{port}")
    print(f"  Concurrency: Multi-threaded (ThreadingHTTPServer + Engine Lock)")
    print(f"  Endpoints:")
    print(f"    - Health: http://{host}:{port}/health")
    print(f"    - Models: http://{host}:{port}/v1/models")
    print(f"    - Chat:   http://{host}:{port}/v1/chat/completions")
    print("=========================================================")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[termux-bitnet] Shutting down server...")
    finally:
        engine.close()
        httpd.server_close()

