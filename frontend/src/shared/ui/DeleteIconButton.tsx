import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import { IconButton, Tooltip } from "@mui/material";
import type { MouseEventHandler } from "react";
import { tokens } from "@/shared/theme/tokens";

interface DeleteIconButtonProps {
  ariaLabel: string;
  tooltip?: string;
  disabled?: boolean;
  onClick: MouseEventHandler<HTMLButtonElement>;
}

/** ファイル・引合の削除操作で共用する、コンパクトな円形アイコンボタン。 */
export function DeleteIconButton({
  ariaLabel,
  tooltip = "削除",
  disabled,
  onClick,
}: DeleteIconButtonProps) {
  return (
    <Tooltip title={tooltip}>
      <span>
        <IconButton
          size="small"
          aria-label={ariaLabel}
          disabled={disabled}
          onClick={onClick}
          sx={{
            width: 32,
            height: 32,
            p: 0.5,
            borderRadius: "50%",
            bgcolor: "transparent",
            "&:hover": { bgcolor: tokens.colors.surface2 },
          }}
        >
          <DeleteOutlineIcon fontSize="small" />
        </IconButton>
      </span>
    </Tooltip>
  );
}
