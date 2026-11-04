import { Shield, Ship, Trophy, Vote } from 'lucide-react'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useSurveillanceStore } from '@/stores/surveillance-store'

const TITANIC_10_CLASSES = [
  { id: 0, name: 'Aircraft Carrier', category: 'Naval Combatant', signature: 'Flat-top flight deck, island superstructure' },
  { id: 1, name: 'Amphibious Assault Ship', category: 'Naval Combatant', signature: 'Well deck, helicopter landing spots, boxy hull' },
  { id: 2, name: 'Destroyer', category: 'Naval Surface', signature: 'Vertical launch systems, phased-array radar masts' },
  { id: 3, name: 'Frigate', category: 'Naval Surface', signature: 'Helo hangar, single radar mast, compact warship hull' },
  { id: 4, name: 'Corvette', category: 'Naval Patrol', signature: 'Fast stealth hull, small displacement (<2,000 tons)' },
  { id: 5, name: 'Submarine', category: 'Subsurface', signature: 'Cylindrical hull, conning tower sail' },
  { id: 6, name: 'Oil Tanker', category: 'Commercial Merchant', signature: 'Long deck, pipeline manifolds, aft bridge island' },
  { id: 7, name: 'Container Ship', category: 'Commercial Merchant', signature: 'Cellular container stacks, high freeboard' },
  { id: 8, name: 'Bulk Carrier', category: 'Commercial Merchant', signature: 'Large rectangular hatch covers, deck cranes' },
  { id: 9, name: 'Cruise Ship', category: 'Commercial Passenger', signature: 'Multi-deck superstructure, passenger balconies' },
]

export function ClassificationFeature() {
  const { droneResult } = useSurveillanceStore()

  const trackSummaries = droneResult?.track_summaries || {}
  const primary = droneResult?.primary_vessel

  return (
    <>
      <Header fixed>
        <div className='flex items-center gap-2'>
          <Ship className='size-5 text-primary' />
          <div>
            <h1 className='text-sm font-bold tracking-normal font-sans text-foreground normal-case'>
              ConvNeXt-Tiny Fine-Grained Vessel Classification
            </h1>
            <p className='text-[10px] font-sans text-muted-foreground'>
              TITANIC-FGS-10 Maritime Dataset | Multi-Frame Temporal Evidence Voting
            </p>
          </div>
        </div>
        <div className='ms-auto flex items-center space-x-2'>
          <Search />
          <ThemeSwitch />
          <ProfileDropdown />
        </div>
      </Header>

      <Main className='space-y-4 p-4 md:p-6'>
        {/* KPI Row */}
        <div className='grid grid-cols-1 sm:grid-cols-3 gap-4'>
          <Card className='bg-card border-border p-4'>
            <div className='flex items-center justify-between text-muted-foreground font-sans text-xs'>
              <span>CURRENT IDENTIFICATION</span>
              <Trophy className='size-4 text-emerald-400' />
            </div>
            <p className='font-sans text-xl font-bold text-emerald-400 mt-2 truncate'>
              {primary?.label || (droneResult ? 'Vessel' : 'AWAITING SEQUENCE')}
            </p>
            <p className='font-sans text-xs text-muted-foreground mt-1'>
              Primary Target ID #{primary?.track_id || 1}
            </p>
          </Card>

          <Card className='bg-card border-border p-4'>
            <div className='flex items-center justify-between text-muted-foreground font-sans text-xs'>
              <span>TEMPORAL EVIDENCE STABILITY</span>
              <Vote className='size-4 text-primary' />
            </div>
            <p className='font-sans text-xl font-bold text-primary mt-2'>
              {primary?.stability ? `${(primary.stability * 100).toFixed(1)}%` : 'N/A'}
            </p>
            <p className='font-sans text-xs text-muted-foreground mt-1'>
              Weighted multi-frame observation share
            </p>
          </Card>

          <Card className='bg-card border-border p-4'>
            <div className='flex items-center justify-between text-muted-foreground font-sans text-xs'>
              <span>CLASSIFIER BACKBONE</span>
              <Shield className='size-4 text-primary' />
            </div>
            <p className='font-sans text-xl font-bold text-primary mt-2'>ConvNeXt-Tiny</p>
            <p className='font-sans text-xs text-muted-foreground mt-1'>
              10-Class Maritime Head | Cross-Entropy
            </p>
          </Card>
        </div>

        {/* Live Track Classifications Table */}
        {Object.keys(trackSummaries).length > 0 && (
          <Card className='bg-card/90 border-border'>
            <CardHeader className='pb-3 border-b border-border/50 flex flex-row items-center justify-between'>
              <div>
                <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground'>
                  Active Mission Track Classifications & Evidence Voting
                </CardTitle>
                <p className='text-[11px] text-muted-foreground font-sans'>
                  Frame-level noisy predictions aggregated into persistent track identities
                </p>
              </div>
              <Badge variant='outline' className='font-sans text-xs text-primary border-primary/40'>
                {Object.keys(trackSummaries).length} TRACKS CLASSIFIED
              </Badge>
            </CardHeader>
            <CardContent className='p-0 overflow-x-auto'>
              <Table>
                <TableHeader>
                  <TableRow className='border-border/60 font-sans text-[11px] text-muted-foreground'>
                    <TableHead>Track ID</TableHead>
                    <TableHead>Assigned Class</TableHead>
                    <TableHead>Evidence Stability</TableHead>
                    <TableHead>Observation Count</TableHead>
                    <TableHead>Classification Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody className='font-sans text-xs'>
                  {Object.entries(trackSummaries).map(([tid, tr]) => {
                    const stab = tr.stability * 100
                    const isConfirmed = tr.classification_status === 'confirmed' || tr.observations >= 3
                    return (
                      <TableRow key={tid} className='border-border/40 hover:bg-muted/40'>
                        <TableCell className='font-bold text-primary'>
                          Track #{String(tr.track_id).padStart(2, '0')}
                        </TableCell>
                        <TableCell className='font-semibold text-foreground'>{tr.label}</TableCell>
                        <TableCell>
                          <span className='px-1.5 py-0.5 rounded text-[11px] bg-red-500/15 text-primary border border-primary/30 font-bold'>
                            {stab.toFixed(1)}%
                          </span>
                        </TableCell>
                        <TableCell className='text-muted-foreground'>{tr.observations} frames</TableCell>
                        <TableCell>
                          <Badge
                            variant='outline'
                            className={`font-sans text-[10px] ${
                              isConfirmed ? 'text-emerald-400 border-emerald-500/40' : 'text-amber-400 border-amber-500/40'
                            }`}
                          >
                            {isConfirmed ? 'CONFIRMED' : 'TENTATIVE'}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}

        {/* TITANIC-FGS-10 Class Catalog Reference */}
        <Card className='bg-card/90 border-border'>
          <CardHeader className='pb-3 border-b border-border/50'>
            <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground'>
              TITANIC-FGS-10 Maritime Vessel Taxonomy
            </CardTitle>
            <p className='text-[11px] text-muted-foreground font-sans'>
              Supervised fine-grained ship categories classified by the ConvNeXt-Tiny feature extractor
            </p>
          </CardHeader>
          <CardContent className='p-0 overflow-x-auto'>
            <Table>
              <TableHeader>
                <TableRow className='border-border/60 font-sans text-[11px] text-muted-foreground'>
                  <TableHead className='w-16'>ID</TableHead>
                  <TableHead>Vessel Class</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Visual Architectural Signature</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody className='font-sans text-xs'>
                {TITANIC_10_CLASSES.map((c) => (
                  <TableRow key={c.id} className='border-border/40 hover:bg-muted/40'>
                    <TableCell className='font-bold text-primary'>{c.id}</TableCell>
                    <TableCell className='font-semibold text-foreground'>{c.name}</TableCell>
                    <TableCell>
                      <span className='text-[11px] text-muted-foreground px-2 py-0.5 rounded bg-muted'>
                        {c.category}
                      </span>
                    </TableCell>
                    <TableCell className='text-muted-foreground'>{c.signature}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </Main>
    </>
  )
}
