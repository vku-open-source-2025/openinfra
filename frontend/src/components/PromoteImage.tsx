import { Link } from 'react-router-dom';

interface PromoteImageProps {
    img: string;
}

const PromoteImage = ({ img }: PromoteImageProps) => {
    return (
        <div className="w-full flex justify-center my-16">
            <div className="relative group max-w-4xl w-full">
                <img
                    src={img}
                    alt="Promotion"
                    className="w-full object-contain transition-all duration-300 group-hover:blur-sm"
                />
                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-black/20 rounded-lg">
                    <Link
                        to="/map"
                        className="px-8 py-3 bg-transparent border-2 border-blue-400 text-white font-bold rounded-full shadow-lg hover:bg-blue-600 hover:border-blue-600 transform hover:scale-105 transition-all backdrop-blur-sm"
                    >
                        Trải nghiệm ngay
                    </Link>
                </div>
            </div>
        </div>
    );
};

export default PromoteImage;
