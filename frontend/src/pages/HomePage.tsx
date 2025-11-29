
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, BarChart3, Droplet, MapPin, Award, Activity } from "lucide-react";
import { getAssets, getLeaderboard } from "../api";
import Footer from "../components/Footer";
import Header from "../components/Header";
import mapImage from "../assets/map.png";

const featureCards = [
    {
        icon: MapPin,
        title: "Bản đồ tương tác",
        description: "Toàn bộ hạ tầng được hiển thị trực quan, thao tác và tìm kiếm ngay trên bản đồ.",
    },
    {
        icon: Droplet,
        title: "Quản lý nước",
        description: "Theo dõi lưu lượng, cảnh báo rò rỉ và lập kế hoạch bảo trì chủ động.",
    },
    {
        icon: BarChart3,
        title: "Phân tích chi tiết",
        description: "Chỉ số vận hành, biểu đồ và thống kê giúp bạn ra quyết định nhanh.",
    },
];

const benefitHighlights = [
    { title: "Giảm thời gian phản ứng", desc: "Phát hiện sự cố nhanh hơn." },
    { title: "Tiết kiệm chi phí", desc: "Tối ưu hóa vận hành hiệu quả." },
    { title: "Độ tin cậy", desc: "Hệ thống giám sát liên tục." },
];

const dashboardImage =
    "https://images.unsplash.com/photo-1553877522-43269d4ea984?auto=format&fit=crop&w=1200&q=80";

const HomePage = () => {
    const [assetCount, setAssetCount] = useState<number | null>(null);
    const [contributorCount, setContributorCount] = useState<number | null>(null);
    const [totalContributions, setTotalContributions] = useState<number | null>(null);
    const [loadingAssets, setLoadingAssets] = useState(false);
    const [loadingLeaderboard, setLoadingLeaderboard] = useState(false);

    useEffect(() => {
        let cancelled = false;
        setLoadingAssets(true);
        setLoadingLeaderboard(true);

        Promise.allSettled([getAssets(), getLeaderboard()]).then((results) => {
            if (cancelled) return;

            const [assetsResult, leaderboardResult] = results;

            if (assetsResult.status === "fulfilled") {
                setAssetCount(assetsResult.value.length);
            } else {
                setAssetCount(null);
            }
            setLoadingAssets(false);

            if (leaderboardResult.status === "fulfilled") {
                const leaderboard = leaderboardResult.value;
                setContributorCount(leaderboard.length);
                const total = leaderboard.reduce((sum, entry) => sum + (entry.count || 0), 0);
                setTotalContributions(total);
            } else {
                setContributorCount(null);
                setTotalContributions(null);
            }
            setLoadingLeaderboard(false);
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

    const statCards = [
        {
            icon: Activity,
            label: "Điểm giám sát đang hoạt động",
            value:
                assetCount !== null
                    ? new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(assetCount)
                    : "—",
            hint: loadingAssets ? "Đang tải..." : "Cập nhật theo dữ liệu mới nhất",
        },
        {
            icon: Award,
            label: "Người đóng góp dữ liệu",
            value:
                contributorCount !== null
                    ? new Intl.NumberFormat("en-US").format(contributorCount)
                    : "—",
            hint: loadingLeaderboard ? "Đang tải..." : "Từ bảng xếp hạng đóng góp",
        },
        {
            icon: BarChart3,
            label: "",
            value:
                totalContributions !== null
                    ? new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(totalContributions)
                    : "—",
            hint: loadingLeaderboard ? "Đang tải..." : "Tổng số lần gửi dữ liệu",
        },
        {
            icon: MapPin,
            label: "Hệ thống đang sử dụng",
            value: "7",
            hint: "7 hệ thống đang sử dụng dịch vụ",
        },
    ];

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
                                <Link
                                    to="/docs"
                                    className="inline-flex items-center justify-center px-6 py-3 border border-slate-200 text-slate-700 rounded-full hover:border-blue hover:text-blue transition-colors"
                                >
                                    Sử dụng API
                                </Link>
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

                {/* Stats Section */}
                <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-10">
                    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 md:p-10">
                        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
                            <div>
                                <div className="text-sm uppercase tracking-wide text-blue-600 font-semibold">Các con số nổi bật</div>
                                <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mt-1">Hiệu quả được chứng minh</h2>
                                <p className="text-slate-600 mt-2">Dữ liệu thu thập, người đóng góp, và hệ thống đang vận hành thực tế.</p>
                            </div>
                        </div>
                        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
                            {statCards.map((item) => (
                                <div
                                    key={item.label || "contributions"}
                                    className="rounded-xl border border-slate-200 bg-gradient-to-br from-white to-slate-50 px-5 py-6 shadow-xs flex flex-col gap-2"
                                >
                                    {item.label && (
                                        <div className="flex items-center gap-3">
                                            <item.icon className="w-5 h-5 text-main-blue" />
                                            <span className="text-sm font-medium text-slate-500">{item.label}</span>
                                        </div>
                                    )}
                                    {!item.label && (
                                        <div className="flex items-center gap-3">
                                            <item.icon className="w-5 h-5 text-main-blue" />
                                            <span className="text-sm font-medium text-slate-500">Đóng góp dữ liệu</span>
                                        </div>
                                    )}
                                    <div className="text-3xl font-bold text-slate-900">{item.value}</div>
                                    <div className="text-xs text-slate-500">{item.hint}</div>
                                </div>
                            ))}
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
                        <p className="text-lg text-white/80">Khám phá bản đồ hạ tầng hoặc tích hợp dữ liệu mở qua API</p>
                        <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
                            <Link
                                to="/map"
                                className="px-8 py-3 bg-white text-main-blue font-semibold rounded-full hover:bg-blue-50 transition-colors"
                            >
                                Khám phá bản đồ
                            </Link>
                            <Link
                                to="/docs"
                                className="px-8 py-3 border border-white text-white font-semibold rounded-full hover:bg-white/10 transition-colors"
                            >
                                Sử dụng API
                            </Link>
                        </div>
                    </div>
                </section>
            </main>
            <Footer />
        </div>
    );
};

export default HomePage;
