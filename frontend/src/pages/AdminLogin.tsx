import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { loginAdmin } from "../api";
import logo from "../assets/map.png"; // reuse existing asset as placeholder logo

const AdminLogin = () => {
    const navigate = useNavigate();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [isAlert, setAlert] = useState(false);
    const [loading, setLoading] = useState(false);

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter") {
            handleLogin();
        }
    };

    const handleLogin = async () => {
        setLoading(true);
        setAlert(false);
        try {
            const data = await loginAdmin(username, password);
            if (data?.token) {
                localStorage.setItem("access-token", data.token);
                navigate("/admin", { replace: true });
            } else {
                setAlert(true);
            }
        } catch (e) {
            setAlert(true);
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
            <div className="flex w-full md:w-4/5 lg:w-3/5 xl:w-1/2 max-w-5xl overflow-hidden rounded-2xl shadow-xl">
                <div className="w-full bg-white p-4 sm:p-6 md:p-8">
                    <div className="mb-6 md:mb-8 flex justify-center">
                        <div className="flex items-center gap-2">
                            <img src={logo} alt="logo" className="h-8 w-auto rounded" />
                            <span className="text-lg font-semibold text-slate-800">OpenInfra Admin</span>
                        </div>
                    </div>

                    <div className="mb-6 md:mb-10 text-center">
                        <h1 className="mb-2 text-xl sm:text-2xl font-semibold text-gray-800">Chào mừng trở lại</h1>
                        <p className="text-sm text-slate-500">Đăng nhập để quản trị hệ thống</p>
                    </div>

                    {isAlert && (
                        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                            Đăng nhập không thành công. Vui lòng kiểm tra lại tài khoản/mật khẩu.
                        </div>
                    )}

                    <div className="space-y-4 sm:space-y-6">
                        <div>
                            <input
                                type="text"
                                placeholder="Tên đăng nhập"
                                className="w-full rounded-lg bg-gray-100 px-4 py-3 text-gray-800 focus:border-main-cyan focus:outline-none focus:ring-1 focus:ring-main-cyan"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                onKeyDown={handleKeyDown}
                            />
                        </div>

                        <div>
                            <input
                                type="password"
                                placeholder="Mật khẩu"
                                className="w-full rounded-lg bg-gray-100 px-4 py-3 text-gray-800 focus:border-main-cyan focus:outline-none focus:ring-1 focus:ring-main-cyan"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                onKeyDown={handleKeyDown}
                            />
                        </div>

                        <div className="text-right">
                            <p className="text-sm text-gray-600">
                                Chưa có tài khoản?{" "}
                                <Link to="/" className="text-main-cyan hover:underline">
                                    Liên hệ quản trị
                                </Link>
                            </p>
                        </div>

                        <button
                            className="flex w-full items-center justify-center rounded-lg bg-gradient-to-r from-[#00e1ff] to-[#33a8ff] py-3 text-center font-medium text-white transition-all hover:shadow-lg disabled:opacity-60"
                            onClick={handleLogin}
                            disabled={loading}
                        >
                            {loading ? "Đang đăng nhập..." : "Đăng nhập"} <ArrowRight className="ml-2 h-4 w-4" />
                        </button>
                    </div>
                </div>
            </div>
        </main>
    );
};

export default AdminLogin;
