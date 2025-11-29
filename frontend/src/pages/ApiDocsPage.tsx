import Header from "../components/Header";
import Footer from "../components/Footer";
import { Code, Database, FileJson, Key, ExternalLink, Copy, Check } from "lucide-react";
import { useState } from "react";

const API_BASE_URL = "https://api.openinfra.space";

const endpoints = [
    {
        method: "GET",
        path: "/api/opendata/",
        title: "API Information",
        description: "Thông tin về API và giấy phép sử dụng dữ liệu",
    },
    {
        method: "GET",
        path: "/api/opendata/assets",
        title: "Danh sách tài sản hạ tầng",
        description: "Lấy tất cả tài sản hạ tầng dưới dạng GeoJSON FeatureCollection (JSON-LD)",
        params: [
            { name: "skip", type: "integer", desc: "Số bản ghi bỏ qua (mặc định: 0)" },
            { name: "limit", type: "integer", desc: "Số bản ghi tối đa (mặc định: 100, tối đa: 1000)" },
            { name: "feature_type", type: "string", desc: "Lọc theo loại hạ tầng" },
            { name: "feature_code", type: "string", desc: "Lọc theo mã hạ tầng" },
        ],
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
    },
    {
        method: "GET",
        path: "/api/opendata/license",
        title: "Thông tin giấy phép",
        description: "Chi tiết về giấy phép ODC-BY",
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

const responseExample = `{
  "@context": {
    "@vocab": "https://schema.org/",
    "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#",
    "geojson": "https://purl.org/geojson/vocab#",
    "Feature": "geojson:Feature",
    "FeatureCollection": "geojson:FeatureCollection",
    ...
  },
  "@type": "FeatureCollection",
  "features": [
    {
      "@type": "Feature",
      "@id": "https://api.openinfra.space/api/opendata/assets/...",
      "geometry": {
        "@type": "Point",
        "coordinates": [108.2544, 15.9748]
      },
      "properties": {
        "feature_type": "Trạm điện",
        "feature_code": "tram_dien",
        "created_at": "2025-11-22T14:27:29.567Z",
        "license": "ODC-BY-1.0",
        "publisher": "VKU.OneLove - OpenInfra"
      }
    }
  ],
  "totalCount": 1250,
  "returned": 10,
  "license": "ODC-BY-1.0",
  "license_url": "https://opendatacommons.org/licenses/by/1-0/"
}`;

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
            className="absolute top-2 right-2 p-2 rounded-md bg-slate-700 hover:bg-slate-600 transition-colors"
            title="Copy to clipboard"
        >
            {copied ? <Check size={16} className="text-green-400" /> : <Copy size={16} className="text-slate-300" />}
        </button>
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
                    <div className="grid md:grid-cols-2 gap-6 mb-12">
                        <a
                            href={`${API_BASE_URL}/api/opendata/assets?limit=5`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-4 p-6 bg-white rounded-xl border border-slate-200 hover:border-green-300 hover:shadow-lg transition-all group"
                        >
                            <div className="p-3 bg-green-100 rounded-lg group-hover:bg-green-200 transition-colors">
                                <FileJson className="text-green-600" size={24} />
                            </div>
                            <div>
                                <h3 className="font-semibold text-slate-900">Try API</h3>
                                <p className="text-sm text-slate-500">Xem dữ liệu mẫu</p>
                            </div>
                            <ExternalLink size={16} className="ml-auto text-slate-400" />
                        </a>

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
                    <h2 className="text-2xl font-bold text-slate-900 mb-8 flex items-center gap-3">
                        <Code size={28} className="text-blue-600" />
                        API Endpoints
                    </h2>

                    <div className="space-y-4">
                        {endpoints.map((endpoint) => (
                            <div
                                key={endpoint.path}
                                className="bg-white rounded-xl border border-slate-200 overflow-hidden"
                            >
                                <div className="p-6">
                                    <div className="flex items-center gap-3 mb-2">
                                        <span className="px-3 py-1 bg-green-100 text-green-700 text-sm font-mono font-semibold rounded">
                                            {endpoint.method}
                                        </span>
                                        <code className="text-slate-800 font-mono">{endpoint.path}</code>
                                    </div>
                                    <h3 className="text-lg font-semibold text-slate-900 mb-1">{endpoint.title}</h3>
                                    <p className="text-slate-600">{endpoint.description}</p>

                                    {endpoint.params && (
                                        <div className="mt-4">
                                            <h4 className="text-sm font-semibold text-slate-700 mb-2">Parameters:</h4>
                                            <div className="bg-slate-50 rounded-lg p-4">
                                                <table className="w-full text-sm">
                                                    <thead>
                                                        <tr className="text-left text-slate-500">
                                                            <th className="pb-2">Tên</th>
                                                            <th className="pb-2">Kiểu</th>
                                                            <th className="pb-2">Mô tả</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody className="text-slate-700">
                                                        {endpoint.params.map((param) => (
                                                            <tr key={param.name}>
                                                                <td className="py-1 font-mono text-blue-600">{param.name}</td>
                                                                <td className="py-1 text-slate-500">{param.type}</td>
                                                                <td className="py-1">{param.desc}</td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
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
                            <CopyButton text={codeExamples[activeTab]} />
                            <pre className="text-sm text-slate-300 overflow-x-auto">
                                <code>{codeExamples[activeTab]}</code>
                            </pre>
                        </div>
                    </div>
                </section>

                {/* Response Example */}
                <section className="max-w-6xl mx-auto px-4 mb-16">
                    <h2 className="text-2xl font-bold text-slate-900 mb-8">Response Example (JSON-LD)</h2>

                    <div className="bg-slate-900 rounded-2xl overflow-hidden">
                        <div className="flex items-center justify-between px-6 py-3 border-b border-slate-700">
                            <span className="text-sm text-slate-400">application/json</span>
                            <CopyButton text={responseExample} />
                        </div>
                        <div className="p-6">
                            <pre className="text-sm text-slate-300 overflow-x-auto">
                                <code>{responseExample}</code>
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
                            Không cần API key. Dữ liệu mở, miễn phí sử dụng với điều kiện ghi nguồn.
                        </p>
                    </div>
                </section>
            </main>
            <Footer />
        </div>
    );
}
