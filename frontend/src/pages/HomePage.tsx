
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, BarChart3, Droplet, MapPin, Network, Shield, Zap } from "lucide-react";
import { getAssets } from "../api";
import Footer from "../components/Footer";
import Header from "../components/Header";
import mapImage from "../assets/map.png";

const featureCards = [
    {
        icon: MapPin,
        title: "Bản đồ tương tác",
        description: "Xem tất cả điểm hạ tầng trên bản đồ với dữ liệu thời gian thực.",
    },
    {
        icon: Zap,
        title: "Giám sát năng lượng",
        description: "Theo dõi tiêu thụ điện năng và phát hiện sự cố nhanh chóng.",
    },
    {
        icon: Droplet,
        title: "Quản lý nước",
        description: "Kiểm soát hệ thống cấp nước và xử lý nước thải.",
    },
    {
        icon: Network,
        title: "Mạng thông tin",
        description: "Giám sát cơ sở hạ tầng mạng và kết nối.",
    },
    {
        icon: BarChart3,
        title: "Phân tích chi tiết",
        description: "Báo cáo toàn diện với biểu đồ và thống kê.",
    },
    {
        icon: Shield,
        title: "An toàn dữ liệu",
        description: "Bảo mật cấp doanh nghiệp cho tất cả thông tin.",
    },
];

const benefitHighlights = [
    { num: "30%", title: "Giảm thời gian phản ứng", desc: "Phát hiện sự cố nhanh hơn." },
    { num: "45%", title: "Tiết kiệm chi phí", desc: "Tối ưu hóa vận hành hiệu quả." },
    { num: "99.9%", title: "Độ tin cậy", desc: "Hệ thống giám sát liên tục." },
];

const dashboardImage =
    "https://images.unsplash.com/photo-1553877522-43269d4ea984?auto=format&fit=crop&w=1200&q=80";

const HomePage = () => {
    const [assetCount, setAssetCount] = useState<number | null>(null);
    const [loadingAssets, setLoadingAssets] = useState(false);

    useEffect(() => {
        let cancelled = false;
        setLoadingAssets(true);
        getAssets()
            .then((assets) => {
                if (!cancelled) {
                    setAssetCount(assets.length);
                }
            })
            .catch(() => {
                if (!cancelled) {
                    setAssetCount(null);
                }
            })
            .finally(() => {
                if (!cancelled) {
                    setLoadingAssets(false);
                }
            });
        return () => {
            cancelled = true;
        };
    }, []);

    const assetCountLabel =
        assetCount !== null
            ? `${new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(assetCount)} Điểm giám sát hoạt động`
            : loadingAssets
                ? "Đang tải điểm giám sát..."
                : "200+ Điểm giám sát hoạt động";

    return (
        <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white text-gray-heading">
            <Header />
            <main className="pt-28">
                {/* Hero Section */}
                <section id="about-us" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24">
                    <div className="grid md:grid-cols-2 gap-12 items-center">
                        <div className="space-y-6">
                            <div className="inline-block px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                                Giải pháp hạ tầng số hoá
                            </div>
                            <h1 className="text-4xl md:text-5xl font-bold text-slate-900 leading-tight">
                                Quản lý hạ tầng thông minh{" "}
                                <span className="bg-gradient-to-r from-main-blue to-main-cyan bg-clip-text text-transparent">
                                    một cách dễ dàng
                                </span>
                            </h1>
                            <p className="text-lg text-slate-600 leading-relaxed">
                                Bản đồ hạ tầng số hoá giúp bạn giám sát, quản lý và tối ưu hóa toàn bộ hệ thống từ
                                một bảng điều khiển trực quan.
                            </p>
                            <div className="flex flex-col sm:flex-row gap-4 pt-2">
                                <Link
                                    to="/map"
                                    className="inline-flex items-center justify-center px-6 py-3 text-white font-semibold rounded-full bg-gradient-to-r from-[#00F2FE] from-21% to-[#4FACFE] shadow-lg hover:shadow-xl transition-shadow"
                                >
                                    Trải nghiệm ngay <ArrowRight className="w-4 h-4 ml-2" />
                                </Link>
                                <a
                                    href="#features"
                                    className="inline-flex items-center justify-center px-6 py-3 border border-slate-200 text-slate-700 rounded-full hover:border-blue hover:text-blue transition-colors"
                                >
                                    Tìm hiểu thêm
                                </a>
                            </div>
                        </div>
                        <div className="relative">
                            <div className="bg-gradient-to-br from-blue-100 to-cyan-100 rounded-2xl p-6 shadow-2xl">
                                <div className="relative overflow-hidden rounded-xl group">
                                    <img
                                        src={mapImage}
                                        alt="Bản đồ hạ tầng"
                                        className="w-full h-full object-cover transition-all duration-300 group-hover:blur-sm"
                                    />
                                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-black/20">
                                        <Link
                                            to="/map"
                                            className="px-8 py-3 bg-white/90 text-blue font-semibold rounded-full shadow-lg hover:bg-white transition-colors backdrop-blur-sm"
                                        >
                                            Trải nghiệm ngay
                                        </Link>
                                    </div>
                                </div>
                            </div>
                            <div className="absolute -bottom-6 -left-6 bg-white rounded-lg p-4 shadow-lg border border-slate-200">
                                <div className="flex items-center gap-3">
                                    <div className="w-3 h-3 rounded-full bg-green-500" />
                                    <span className="text-sm font-medium text-slate-700">{assetCountLabel}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Features Section */}
                <section id="features" className="bg-slate-900 text-white py-20">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="text-center mb-16">
                            <h2 className="text-3xl md:text-4xl font-bold mb-4">Tính năng chính</h2>
                            <p className="text-lg text-slate-400">Tất cả những gì bạn cần để quản lý hạ tầng hiệu quả</p>
                        </div>
                        <div className="grid md:grid-cols-3 gap-8">
                            {featureCards.map((feature, index) => (
                                <div
                                    key={feature.title + index}
                                    className="bg-slate-800 border border-slate-700 rounded-xl p-6 hover:border-blue transition-colors"
                                >
                                    <feature.icon className="w-8 h-8 text-cyan mb-4" />
                                    <h3 className="text-xl font-semibold text-white mb-2">{feature.title}</h3>
                                    <p className="text-slate-400">{feature.description}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                {/* Benefits Section */}
                <section id="benefits" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">Lợi ích</h2>
                        <p className="text-lg text-slate-600">Tối ưu hóa quản lý hạ tầng của bạn</p>
                    </div>
                    <div className="grid md:grid-cols-2 gap-12">
                        <div className="space-y-6">
                            {benefitHighlights.map((item) => (
                                <div key={item.title} className="flex gap-4">
                                    <div className="text-3xl font-bold text-main-blue">{item.num}</div>
                                    <div>
                                        <h3 className="font-semibold text-slate-900">{item.title}</h3>
                                        <p className="text-slate-600">{item.desc}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-2xl p-8 border border-blue-200 shadow-md">
                            <img src={dashboardImage} alt="Bảng điều khiển" className="rounded-lg w-full object-cover" />
                        </div>
                    </div>
                </section>

                {/* CTA Section */}
                <section className="bg-gradient-to-r from-main-blue to-main-cyan text-white py-16">
                    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
                        <h2 className="text-3xl md:text-4xl font-bold">Sẵn sàng bắt đầu?</h2>
                        <p className="text-lg text-white/80">Tham gia hàng ngàn tổ chức đang hiện đại hóa hạ tầng của họ</p>
                        <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
                            <Link
                                to="/map"
                                className="px-8 py-3 bg-white text-main-blue font-semibold rounded-full hover:bg-blue-50 transition-colors"
                            >
                                Yêu cầu Demo
                            </Link>
                            <a
                                href="#benefits"
                                className="px-8 py-3 border border-white text-white font-semibold rounded-full hover:bg-white/10 transition-colors"
                            >
                                Tìm hiểu thêm
                            </a>
                        </div>
                    </div>
                </section>
            </main>
            <Footer />
        </div>
    );
};

export default HomePage;
