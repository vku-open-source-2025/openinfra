
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, BarChart3, Droplet, MapPin, Award, Activity } from "lucide-react";
import { getAssets, getLeaderboard } from "../api";
import Footer from "../components/Footer";
import Header from "../components/Header";
import mapImage from "../assets/map.png";

const featureCards = [
    {
        icon: MapPin,        title: "Interactive Map",
        description: "All infrastructure displayed visually, with interactive search and navigation on the map.",
    },
    {
        icon: Droplet,
        title: "Water Management",
        description: "Monitor flow rates, leak alerts, and proactive maintenance planning.",
    },
    {
        icon: BarChart3,
        title: "Detailed Analytics",
        description: "Operational metrics, charts, and statistics to help you make quick decisions.",
    },
];

const benefitHighlights = [
    { title: "Reduce Response Time", desc: "Detect issues faster." },
    { title: "Cost Savings", desc: "Optimize operations efficiently." },
    { title: "Reliability", desc: "Continuous monitoring system." },
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
            ? `${new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(assetCount)} Active monitoring points`
            : loadingAssets
                ? "Loading monitoring points..."
                : "200+ Active monitoring points";

    const statCards = [
        {
            icon: Activity,
            label: "Active Monitoring Points",
            value:
                assetCount !== null
                    ? new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(assetCount)
                    : "—",
            hint: loadingAssets ? "Loading..." : "Updated with latest data",
            color: "from-cyan-500 to-blue-500",
            bgColor: "from-cyan-50 to-blue-50",
            iconColor: "text-cyan-500",
        },
        {
            icon: Award,
            label: "Data Contributors",
            value:
                contributorCount !== null
                    ? new Intl.NumberFormat("en-US").format(contributorCount)
                    : "—",
            hint: loadingLeaderboard ? "Loading..." : "From contribution leaderboard",
            color: "from-amber-500 to-orange-500",
            bgColor: "from-amber-50 to-orange-50",
            iconColor: "text-amber-500",
        },
        {
            icon: BarChart3,
            label: "Data Contributions",
            value:
                totalContributions !== null
                    ? new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(totalContributions)
                    : "—",
            hint: loadingLeaderboard ? "Loading..." : "Total data submissions",
            color: "from-emerald-500 to-teal-500",
            bgColor: "from-emerald-50 to-teal-50",
            iconColor: "text-emerald-500",
        },
        {
            icon: MapPin,
            label: "Systems in Use",
            value: "7",
            hint: "7 systems currently using the service",
            color: "from-purple-500 to-pink-500",
            bgColor: "from-purple-50 to-pink-50",
            iconColor: "text-purple-500",
        },
    ];

    return (
        <div className="min-h-screen bg-white text-gray-heading">
            <Header />
            <main className="pt-28">
                {/* Hero Section */}
                <section id="about-us" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24">
                    <div className="grid md:grid-cols-2 gap-12 items-center">
                        <div className="space-y-6">
                            <div className="inline-block px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                                Digital Infrastructure Solution
                            </div>
                            <h1 className="text-4xl md:text-5xl font-bold text-slate-900 leading-tight">
                                Smart Infrastructure Management{" "}
                                <span className="bg-gradient-to-r from-main-blue to-main-cyan bg-clip-text text-transparent">
                                    Made Easy
                                </span>
                            </h1>
                            <p className="text-lg text-slate-600 leading-relaxed">
                                Digital infrastructure map helps you monitor, manage, and optimize your entire system from
                                an intuitive dashboard.
                            </p>
                            <div className="flex flex-col sm:flex-row gap-4 pt-2">
                                <Link
                                    to="/map"
                                    className="inline-flex items-center justify-center px-6 py-3 text-white font-semibold rounded-full bg-gradient-to-r from-[#00F2FE] from-21% to-[#4FACFE] shadow-lg hover:shadow-xl transition-shadow"
                                >
                                    Try it now <ArrowRight className="w-4 h-4 ml-2" />
                                </Link>
                                <Link
                                    to="/docs"
                                    className="inline-flex items-center justify-center px-6 py-3 border border-slate-200 text-slate-700 rounded-full hover:border-blue hover:text-blue transition-colors"
                                >
                                    Use API
                                </Link>
                            </div>
                        </div>
                        <div className="relative">
                            <div className="bg-gradient-to-br from-blue-100 to-cyan-100 rounded-2xl p-6 shadow-2xl">
                                <div className="relative overflow-hidden rounded-xl group">
                                    <img
                                        src={mapImage}
                                        alt="Infrastructure Map"
                                        className="w-full h-full object-cover transition-all duration-300 group-hover:blur-sm"
                                    />
                                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-black/20">
                                        <Link
                                            to="/map"
                                            className="px-8 py-3 bg-white/90 text-blue font-semibold rounded-full shadow-lg hover:bg-white transition-colors backdrop-blur-sm"
                                        >
                                            Try it now
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
                                <div className="text-sm uppercase tracking-wide text-blue-600 font-semibold">Key Numbers</div>
                                <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mt-1">Proven Effectiveness</h2>
                                <p className="text-slate-600 mt-2">Data collected, contributors, and systems operating in real-time.</p>
                            </div>
                        </div>
                        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
                            {statCards.map((item) => (
                                <div
                                    key={item.label}
                                    className={`rounded-xl border border-slate-200 bg-gradient-to-br ${item.bgColor} px-5 py-6 shadow-sm hover:shadow-md transition-shadow flex flex-col gap-2 relative overflow-hidden`}
                                >
                                    {/* Decorative gradient bar */}
                                    <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${item.color}`}></div>
                                    
                                    <div className="flex items-center gap-3">
                                        <div className={`p-2 rounded-lg bg-white/80 shadow-sm`}>
                                            <item.icon className={`w-5 h-5 ${item.iconColor}`} />
                                        </div>
                                        <span className="text-sm font-medium text-slate-600">{item.label}</span>
                                    </div>
                                    <div className={`text-3xl font-bold bg-gradient-to-r ${item.color} bg-clip-text text-transparent`}>
                                        {item.value}
                                    </div>
                                    <div className="text-xs text-slate-500">{item.hint}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                {/* Features Section */}
                <section id="features" className="bg-white py-20">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="text-center mb-16">
                            <h2 className="text-3xl md:text-4xl font-bold mb-4 text-slate-900">Key Features</h2>
                            <p className="text-lg text-slate-600">Everything you need to manage infrastructure efficiently</p>
                        </div>
                        <div className="grid md:grid-cols-3 gap-8">
                            {featureCards.map((feature, index) => (
                                <div
                                    key={feature.title + index}
                                    className="bg-white border border-slate-200 rounded-xl p-6 hover:border-[#4FACFE] hover:shadow-lg transition-all"
                                >
                                    <feature.icon className="w-8 h-8 text-[#4FACFE] mb-4" />
                                    <h3 className="text-xl font-semibold text-slate-900 mb-2">{feature.title}</h3>
                                    <p className="text-slate-600">{feature.description}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                {/* Benefits Section */}
                <section id="benefits" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">Benefits</h2>
                        <p className="text-lg text-slate-600">Optimize your infrastructure management</p>
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
                            <img src={dashboardImage} alt="Dashboard" className="rounded-lg w-full object-cover" />
                        </div>
                    </div>
                </section>

                {/* CTA Section */}
                <section className="bg-white py-20">
                    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-8">
                        <h2 className="text-3xl md:text-5xl font-bold text-slate-900">Try it now</h2>
                        <p className="text-xl text-slate-600 max-w-2xl mx-auto">
                            Explore the visual infrastructure map or integrate open data into your application via API
                        </p>
                        <div className="flex flex-col sm:flex-row gap-6 justify-center pt-6">
                            <Link
                                to="/map"
                                className="inline-flex items-center justify-center px-10 py-4 text-white font-bold text-lg rounded-full bg-gradient-to-r from-[#00F2FE] from-21% to-[#4FACFE] shadow-lg hover:shadow-xl transition-all transform hover:scale-105"
                            >
                                Explore Map →
                            </Link>
                            <Link
                                to="/docs"
                                className="inline-flex items-center justify-center px-10 py-4 border-2 border-slate-300 text-slate-700 font-bold text-lg rounded-full hover:border-[#4FACFE] hover:text-[#4FACFE] transition-all transform hover:scale-105"
                            >
                                Use API
                            </Link>
                        </div>
                    </div>
                </section>

                {/* Contribute Section */}
                <section className="bg-slate-50 py-20">
                    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-8">
                        <div className="inline-block px-4 py-1 bg-cyan-100 text-cyan-700 rounded-full text-sm font-medium mb-4">
                            Open Source
                        </div>
                        <h2 className="text-3xl md:text-5xl font-bold text-slate-900">Contribute to Us</h2>
                        <p className="text-xl text-slate-600 max-w-2xl mx-auto">
                            OpenInfra is an open source project. You can contribute code, report bugs, or add infrastructure data to help build the community.
                        </p>
                        <div className="flex flex-col sm:flex-row gap-6 justify-center pt-6">
                            <a
                                href="https://github.com/vku-open-source-2025/openinfra"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center justify-center gap-3 px-10 py-4 bg-white text-slate-900 font-bold text-lg rounded-full hover:bg-slate-100 transition-all transform hover:scale-105"
                            >
                                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                                    <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                                </svg>
                                Source Code
                            </a>
                            <a
                                href="https://contribution.openinfra.space/"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center justify-center gap-3 px-10 py-4 border-2 border-slate-300 text-slate-700 font-bold text-lg rounded-full hover:border-[#4FACFE] hover:text-[#4FACFE] transition-all transform hover:scale-105"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                                </svg>
                                Contribute Data
                            </a>
                        </div>
                        {/* License Links */}
                        <div className="flex flex-wrap items-center justify-center gap-6 pt-4 text-sm text-slate-500">
                            <a
                                href="https://github.com/vku-open-source-2025/openinfra/blob/main/LICENSE"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="hover:text-[#4FACFE] transition-colors"
                            >
                                Code: Apache 2.0
                            </a>
                            <span className="text-slate-300">|</span>
                            <a
                                href="https://opendatacommons.org/licenses/by/1-0/"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="hover:text-[#4FACFE] transition-colors"
                            >
                                Data: ODC-BY
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
