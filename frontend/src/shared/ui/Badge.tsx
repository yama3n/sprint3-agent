import { Box } from "@mui/material";
import { tokens } from "@/shared/theme/tokens";

export type BadgeVariant = "neutral" | "success" | "review" | "web";

const VARIANT_STYLES: Record<
  BadgeVariant,
  { bg: string; color: string; border: string }
> = {
  neutral: {
    bg: tokens.colors.surface2,
    color: tokens.colors.text.secondary,
    border: tokens.colors.borderStrong,
  },
  success: {
    bg: tokens.colors.status.success.bg,
    color: tokens.colors.status.success.text,
    border: tokens.colors.status.success.border,
  },
  review: {
    bg: tokens.colors.status.review.bg,
    color: tokens.colors.status.review.text,
    border: tokens.colors.status.review.border,
  },
  web: {
    bg: tokens.colors.status.web.bg,
    color: tokens.colors.status.web.text,
    border: tokens.colors.status.web.border,
  },
};

interface BadgeProps {
  variant: BadgeVariant;
  children: React.ReactNode;
  withDot?: boolean;
}

/** mockup.html .badge 相当。要確認理由は問わずreview 1色に統一する（03-spec 4章）。 */
export function Badge({ variant, children, withDot = false }: BadgeProps) {
  const style = VARIANT_STYLES[variant];
  return (
    <Box
      component="span"
      sx={{
        display: "inline-flex",
        alignItems: "center",
        gap: "5px",
        px: "10px",
        py: "3px",
        borderRadius: "12px",
        fontSize: "11.5px",
        fontWeight: 600,
        bgcolor: style.bg,
        color: style.color,
        border: `1px solid ${style.border}`,
      }}
    >
      {withDot ? (
        <Box
          component="span"
          sx={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            bgcolor: "currentColor",
            flexShrink: 0,
          }}
        />
      ) : null}
      {children}
    </Box>
  );
}
