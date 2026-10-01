interface StatusDotProps {
  online: boolean;
  size?: "sm" | "md";
  label?: string;
}

export default function StatusDot({ online, size = "sm", label }: StatusDotProps) {
  const dotSize = size === "sm" ? "h-2 w-2" : "h-2.5 w-2.5";
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="relative flex">
        {online && (
          <span
            className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-60 ${
              online ? "bg-emerald-400" : ""
            }`}
          />
        )}
        <span
          className={`relative inline-flex ${dotSize} rounded-full ${
            online ? "bg-emerald-500" : "bg-red-500"
          }`}
        />
      </span>
      {label && (
        <span className="text-xs text-gray-500 dark:text-gray-400">{label}</span>
      )}
    </span>
  );
}
