const Footer = () => {
    return (
        <footer className="bg-slate-900 text-slate-400 py-12 border-t border-slate-800">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="grid md:grid-cols-4 gap-8 mb-8">
                    <div>
                        <div className="flex items-center gap-2 mb-4">
                            <div className="w-6 h-6 bg-gradient-to-br from-main-blue to-main-cyan rounded-lg" />
                            <span className="font-bold text-white">OpenInfra</span>
                        </div>
                        <p className="text-sm">Giải pháp quản lý hạ tầng số hoá</p>
                    </div>
                    <div>
                        <h4 className="font-semibold text-white mb-4">Sản phẩm</h4>
                        <ul className="space-y-2 text-sm">
                            <li>
                                <a href="#features" className="hover:text-white transition-colors">
                                    Bản đồ hạ tầng
                                </a>
                            </li>
                            <li>
                                <a href="#benefits" className="hover:text-white transition-colors">
                                    Giám sát
                                </a>
                            </li>
                            <li>
                                <a href="#benefits" className="hover:text-white transition-colors">
                                    Phân tích
                                </a>
                            </li>
                        </ul>
                    </div>
                    <div>
                        <h4 className="font-semibold text-white mb-4">Công ty</h4>
                        <ul className="space-y-2 text-sm">
                            <li>
                                <a href="#about-us" className="hover:text-white transition-colors">
                                    Về chúng tôi
                                </a>
                            </li>
                            <li>
                                <a href="#benefits" className="hover:text-white transition-colors">
                                    Blog
                                </a>
                            </li>
                            <li>
                                <a href="#benefits" className="hover:text-white transition-colors">
                                    Tuyển dụng
                                </a>
                            </li>
                        </ul>
                    </div>
                    <div>
                        <h4 className="font-semibold text-white mb-4">Pháp lý</h4>
                        <ul className="space-y-2 text-sm">
                            <li>
                                <a href="#benefits" className="hover:text-white transition-colors">
                                    Quyền riêng tư
                                </a>
                            </li>
                            <li>
                                <a href="#benefits" className="hover:text-white transition-colors">
                                    Điều khoản
                                </a>
                            </li>
                            <li>
                                <a href="#benefits" className="hover:text-white transition-colors">
                                    Liên hệ
                                </a>
                            </li>
                        </ul>
                    </div>
                </div>
                <div className="border-t border-slate-800 pt-8 flex flex-col sm:flex-row justify-between items-center gap-4">
                    <p className="text-sm">© 2025 OpenInfra. Bản quyền được bảo lưu.</p>
                    <div className="flex gap-6 text-sm">
                        <a href="#" className="hover:text-white transition-colors">
                            Twitter
                        </a>
                        <a href="#" className="hover:text-white transition-colors">
                            LinkedIn
                        </a>
                        <a href="#" className="hover:text-white transition-colors">
                            GitHub
                        </a>
                    </div>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
