import * as React from 'react'
import { cn } from '@/lib/utils'

export interface SliderProps {
  min?: number
  max?: number
  step?: number
  value?: number[]
  defaultValue?: number[]
  onValueChange?: (value: number[]) => void
  disabled?: boolean
  className?: string
}

export function Slider({
  min = 0,
  max = 100,
  step = 1,
  value,
  defaultValue = [0],
  onValueChange,
  disabled = false,
  className,
}: SliderProps) {
  const currentVal = value !== undefined ? value[0] : defaultValue[0]

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVal = parseFloat(e.target.value)
    onValueChange?.([newVal])
  }

  return (
    <div
      className={cn(
        'relative flex w-full touch-none select-none items-center',
        className
      )}
    >
      <input
        type='range'
        min={min}
        max={max}
        step={step}
        value={currentVal}
        disabled={disabled}
        onChange={handleChange}
        className='w-full h-2 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50'
      />
    </div>
  )
}
