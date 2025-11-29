import Header from "../components/Header";
import Footer from "../components/Footer";
import { Code, Database, Key, ExternalLink, Copy, Check, Play, Loader2, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

const API_BASE_URL = "https://api.openinfra.space";

interface EndpointParam {
    name: string;
    type: string;
    desc: string;
    default?: string;
}

interface Endpoint {
    method: string;
    path: string;
    title: string;
    description: string;
    params?: EndpointParam[];
    testPath?: string;
}

const endpoints: Endpoint[] = [
    {
        method: "GET",
        path: "/api/opendata/",
        title: "API Information",
        description: "Thông tin về API và giấy phép sử dụng dữ liệu",
        testPath: "/api/opendata/",
    },
    {
        method: "GET",
        path: "/api/opendata/assets",
        title: "Danh sách tài sản hạ tầng",
        description: "Lấy tất cả tài sản hạ tầng dưới dạng GeoJSON FeatureCollection (JSON-LD)",
        params: [
            { name: "skip", type: "integer", desc: "Số bản ghi bỏ qua (mặc định: 0)", default: "0" },
            { name: "limit", type: "integer", desc: "Số bản ghi tối đa (mặc định: 100, tối đa: 1000)", default: "5" },
            { name: "feature_type", type: "string", desc: "Lọc theo loại hạ tầng" },
            { name: "feature_code", type: "string", desc: "Lọc theo mã hạ tầng" },
        ],
        testPath: "/api/opendata/assets?limit=5",
    },
    {
        method: "GET",
        path: "/api/opendata/assets/{asset_id}",
        title: "Chi tiết tài sản",
        description: "Lấy thông tin chi tiết một tài sản theo ID",
        params: [{ name: "asset_id", type: "string", desc: "ID của tài sản (MongoDB ObjectId)" }],
    },
    {
        method: "GET",
        path: "/api/opendata/feature-types",
        title: "Danh sách loại hạ tầng",
        description: "Lấy tất cả các loại hạ tầng có sẵn và số lượng tương ứng",
        testPath: "/api/opendata/feature-types",
    },
    {
        method: "GET",
        path: "/api/opendata/license",
        title: "Thông tin giấy phép",
        description: "Chi tiết về giấy phép ODC-BY",
        testPath: "/api/opendata/license",
    },
];

const codeExamples = {
    curl: `curl -X GET "${API_BASE_URL}/api/opendata/assets?limit=10" \\
  -H "Accept: application/json"`,
    javascript: `// Sử dụng fetch API
const response = await fetch('${API_BASE_URL}/api/opendata/assets?limit=10');
const data = await response.json();

// Dữ liệu trả về là GeoJSON FeatureCollection với JSON-LD context
console.log(data.features);
console.log('License:', data.license);`,
    python: `import requests

response = requests.get(
    '${API_BASE_URL}/api/opendata/assets',
    params={'limit': 10, 'feature_type': 'Trạm điện'}
)
data = response.json()

# Dữ liệu GeoJSON với JSON-LD context
for feature in data['features']:
    print(feature['properties']['feature_type'])
    print(feature['geometry']['coordinates'])`,
};

function CopyButton({ text }: { text: string }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <button
            onClick={handleCopy}
            className="p-2 rounded-md bg-slate-700 hover:bg-slate-600 transition-colors"
            title="Copy to clipboard"
        >
            {copied ? <Check size={16} className="text-green-400" /> : <Copy size={16} className="text-slate-300" />}
        </button>
    );
}

function EndpointCard({ endpoint }: { endpoint: Endpoint }) {
    const [isLoading, setIsLoading] = useState(false);
    const [response, setResponse] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [showResponse, setShowResponse] = useState(false);
    const [assetId, setAssetId] = useState("");

    const canTest = endpoint.testPath || (endpoint.path.includes("{asset_id}") && assetId);

    const handleTest = async () => {
        setIsLoading(true);
        setError(null);
        setResponse(null);
        setShowResponse(true);

        try {
            let testUrl = API_BASE_URL;
            if (endpoint.testPath) {
                testUrl += endpoint.testPath;
            } else if (endpoint.path.includes("{asset_id}") && assetId) {
                testUrl += endpoint.path.replace("{asset_id}", assetId);
            } else {
                setError("Vui lòng nhập asset_id để test");
                setIsLoading(false);
                return;
            }

            const res = await fetch(testUrl);
            const data = await res.json();
            setResponse(JSON.stringify(data, null, 2));
        } catch (err) {
            setError(err instanceof Error ? err.message : "Có lỗi xảy ra");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="p-6">
                <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                    <div className="flex items-center gap-3">
                        <span className="px-3 py-1 bg-green-100 text-green-700 text-sm font-mono font-semibold rounded">
                            {endpoint.method}
                        </span>
                        <code className="text-slate-800 font-mono text-sm">{endpoint.path}</code>
                    </div>
                    {endpoint.testPath && (
                        <button
                            onClick={handleTest}
                            disabled={isLoading}
                            className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#00F2FE] to-[#4FACFE] text-white font-medium rounded-lg hover:shadow-lg transition-all disabled:opacity-50"
                        >
                            {isLoading ? (
                                <Loader2 size={16} className="animate-spin" />
                            ) : (
                                <Play size={16} />
                            )}
                            Test
                        </button>
                    )}
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-1">{endpoint.title}</h3>
                <p className="text-slate-600">{endpoint.description}</p>

                {endpoint.params && (
                    <div className="mt-4">
                        <h4 className="text-sm font-semibold text-slate-700 mb-2">Parameters:</h4>
                        <div className="bg-slate-50 rounded-lg p-4 overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="text-left text-slate-500">
                                        <th className="pb-2 pr-4">Tên</th>
                                        <th className="pb-2 pr-4">Kiểu</th>
                                        <th className="pb-2">Mô tả</th>
                                    </tr>
                                </thead>
                                <tbody className="text-slate-700">
                                    {endpoint.params.map((param) => (
                                        <tr key={param.name}>
                                            <td className="py-1 pr-4 font-mono text-blue-600">{param.name}</td>
                                            <td className="py-1 pr-4 text-slate-500">{param.type}</td>
                                            <td className="py-1">{param.desc}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* Input for asset_id if needed */}
                {endpoint.path.includes("{asset_id}") && (
                    <div className="mt-4">
                        <label className="block text-sm font-medium text-slate-700 mb-2">
                            Nhập asset_id để test:
                        </label>
                        <p className="text-xs text-slate-500 mb-2">
                            Mẫu: <code 
                                className="bg-slate-100 px-2 py-1 rounded cursor-pointer hover:bg-slate-200 transition-colors"
                                onClick={() => setAssetId("6927235efbcca60d69c3bf97")}
                                title="Click để sử dụng ID mẫu"
                            >6927235efbcca60d69c3bf97</code>
                        </p>
                        <div className="flex gap-2">
                            <input
                                type="text"
                                value={assetId}
                                onChange={(e) => setAssetId(e.target.value)}
                                placeholder="6927235efbcca60d69c3bf97"
                                className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                            <button
                                onClick={handleTest}
                                disabled={isLoading || !assetId}
                                className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#00F2FE] to-[#4FACFE] text-white font-medium rounded-lg hover:shadow-lg transition-all disabled:opacity-50"
                            >
                                {isLoading ? (
                                    <Loader2 size={16} className="animate-spin" />
                                ) : (
                                    <Play size={16} />
                                )}
                                Test
                            </button>
                        </div>
                    </div>
                )}

                {/* Response Section */}
                {showResponse && (
                    <div className="mt-4">
                        <button
                            onClick={() => setShowResponse(!showResponse)}
                            className="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-900 mb-2"
                        >
                            {showResponse ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                            Response
                        </button>
                        <div className="bg-slate-900 rounded-lg overflow-hidden">
                            <div className="flex items-center justify-between px-4 py-2 border-b border-slate-700">
                                <span className="text-xs text-slate-400">
                                    {error ? "Error" : "application/json"}
                                </span>
                                {response && <CopyButton text={response} />}
                            </div>
                            <div className="p-4 max-h-96 overflow-auto">
                                {isLoading && (
                                    <div className="flex items-center justify-center py-8">
                                        <Loader2 size={24} className="animate-spin text-blue-400" />
                                    </div>
                                )}
                                {error && (
                                    <p className="text-red-400 text-sm">{error}</p>
                                )}
                                {response && (
                                    <pre className="text-sm text-slate-300 overflow-x-auto">
                                        <code>{response}</code>
                                    </pre>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default function ApiDocsPage() {
    const [activeTab, setActiveTab] = useState<"curl" | "javascript" | "python">("javascript");

    return (
        <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
            <Header />
            <main className="pt-24 pb-16">
                {/* Hero Section */}
                <section className="max-w-6xl mx-auto px-4 mb-16">
                    <div className="text-center mb-12">
                        <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-700 px-4 py-2 rounded-full text-sm font-medium mb-4">
                            <Database size={16} />
                            Open Data API
                        </div>
                        <h1 className="text-4xl md:text-5xl font-bold text-slate-900 mb-4">
                            API Documentation
                        </h1>
                        <p className="text-xl text-slate-600 max-w-2xl mx-auto">
                            Truy cập dữ liệu hạ tầng GIS mở theo chuẩn JSON-LD. 
                            Miễn phí sử dụng với giấy phép ODC-BY.
                        </p>
                    </div>

                    {/* Quick Links */}
                    <div className="flex justify-center mb-12">
                        <a
                            href="https://opendatacommons.org/licenses/by/1-0/"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-4 p-6 bg-white rounded-xl border border-slate-200 hover:border-amber-300 hover:shadow-lg transition-all group"
                        >
                            <div className="p-3 bg-amber-100 rounded-lg group-hover:bg-amber-200 transition-colors">
                                <Key className="text-amber-600" size={24} />
                            </div>
                            <div>
                                <h3 className="font-semibold text-slate-900">ODC-BY License</h3>
                                <p className="text-sm text-slate-500">Điều khoản sử dụng</p>
                            </div>
                            <ExternalLink size={16} className="ml-auto text-slate-400" />
                        </a>
                    </div>
                </section>

                {/* License Notice */}
                <section className="max-w-6xl mx-auto px-4 mb-16">
                    <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-2xl p-8">
                        <div className="flex items-start gap-4">
                            <Key className="text-amber-600 shrink-0 mt-1" size={24} />
                            <div>
                                <h2 className="text-xl font-bold text-slate-900 mb-2">
                                    Giấy phép ODC-BY (Open Data Commons Attribution)
                                </h2>
                                <p className="text-slate-700">
                                    Dữ liệu được cung cấp miễn phí theo{" "}
                                    <a 
                                        href="https://opendatacommons.org/licenses/by/1-0/" 
                                        target="_blank" 
                                        rel="noopener noreferrer"
                                        className="text-blue-600 hover:underline font-medium"
                                    >
                                        giấy phép ODC-BY
                                    </a>.
                                </p>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Endpoints */}
                <section className="max-w-6xl mx-auto px-4 mb-16">
                    <h2 className="text-2xl font-bold text-slate-900 mb-2 flex items-center gap-3">
                        <Code size={28} className="text-blue-600" />
                        API Endpoints
                    </h2>
                    <p className="text-slate-500 mb-8">
                        Bấm nút <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gradient-to-r from-[#00F2FE] to-[#4FACFE] text-white text-xs font-medium rounded"><Play size={12} /> Test</span> để thử nghiệm trực tiếp
                    </p>

                    <div className="space-y-4">
                        {endpoints.map((endpoint) => (
                            <EndpointCard key={endpoint.path} endpoint={endpoint} />
                        ))}
                    </div>
                </section>

                {/* Code Examples */}
                <section className="max-w-6xl mx-auto px-4 mb-16">
                    <h2 className="text-2xl font-bold text-slate-900 mb-8">Code Examples</h2>

                    <div className="bg-slate-900 rounded-2xl overflow-hidden">
                        <div className="flex border-b border-slate-700">
                            {(["javascript", "python", "curl"] as const).map((tab) => (
                                <button
                                    key={tab}
                                    onClick={() => setActiveTab(tab)}
                                    className={`px-6 py-3 text-sm font-medium transition-colors ${
                                        activeTab === tab
                                            ? "bg-slate-800 text-white"
                                            : "text-slate-400 hover:text-white"
                                    }`}
                                >
                                    {tab.charAt(0).toUpperCase() + tab.slice(1)}
                                </button>
                            ))}
                        </div>
                        <div className="relative p-6">
                            <div className="absolute top-2 right-2">
                                <CopyButton text={codeExamples[activeTab]} />
                            </div>
                            <pre className="text-sm text-slate-300 overflow-x-auto">
                                <code>{codeExamples[activeTab]}</code>
                            </pre>
                        </div>
                    </div>
                </section>

                {/* Base URL Info */}
                <section className="max-w-6xl mx-auto px-4">
                    <div className="bg-blue-50 border border-blue-200 rounded-2xl p-8 text-center">
                        <h3 className="text-lg font-semibold text-slate-900 mb-2">Base URL</h3>
                        <code className="text-xl text-blue-600 font-mono bg-white px-4 py-2 rounded-lg border">
                            {API_BASE_URL}
                        </code>
                        <p className="text-slate-600 mt-4">
                            Không cần API key. Dữ liệu mở, miễn phí sử dụng.
                        </p>
                    </div>
                </section>
            </main>
            <Footer />
        </div>
    );
}
