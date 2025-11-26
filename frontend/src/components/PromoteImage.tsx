interface PromoteImageProps {
    img: string;
}

const PromoteImage = ({ img }: PromoteImageProps) => {
    return (
        <div className="w-full flex justify-center my-16">
            <img src={img} alt="Promotion" className="max-w-4xl w-full object-contain" />
        </div>
    );
};

export default PromoteImage;
