import { useNavigate } from 'react-router-dom';

const LandingPanel = () => {
    const navigate = useNavigate();

    return (
        <div className="bg-gradient-to-r from-[#00F2FE] from-21% to-[#4FACFE] py-20 my-16">
            <div className="max-w-4xl mx-auto text-center px-4">
                <h2 className="text-4xl font-bold text-white mb-6">
                    Sẵn sàng quản lý hạ tầng của bạn?
                </h2>
                <p className="text-white text-lg mb-8">
                    Bắt đầu giám sát và bảo trì tài sản hạ tầng với dữ liệu IoT thời gian thực
                </p>
                <button
                    onClick={() => navigate('/admin')}
                    className="bg-white text-[#4FACFE] font-semibold px-10 py-3 rounded-full hover:shadow-lg transition-shadow"
                >
                    Bắt đầu ngay
                </button>
            </div>
        </div>
    );
};

export default LandingPanel;
