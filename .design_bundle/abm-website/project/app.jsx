// Mounts the design canvas with the single chosen direction (E).
// Tweaks panel exposes mode (light/dark) and accent (red-blue / b&w).

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": "red-blue",
  "mode": "light"
}/*EDITMODE-END*/;

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const useAccent = t.accent === 'red-blue';

  return (
    <React.Fragment>
      <DesignCanvas title="ABM · Political Polarization" subtitle="Wireframes for the polarlab interactive paper">

        <DCSection id="combined" title="Direction E" subtitle="Landing + fullscreen views. Modern minimalist, FT-flavoured.">
          <DCArtboard id="E-landing" label="E · Landing" width={1440} height={1180}>
            <WireframeE accent={useAccent} mode={t.mode} />
          </DCArtboard>
          <DCArtboard id="E-full" label="E · Fullscreen" width={1440} height={900}>
            <WireframeEFull accent={useAccent} mode={t.mode} />
          </DCArtboard>
        </DCSection>

      </DesignCanvas>

      <TweaksPanel title="Wireframe tweaks">
        <TweakRadio label="Mode" value={t.mode}
          options={['light', 'dark']}
          onChange={(v) => setTweak('mode', v)} />
        <TweakRadio label="Accent" value={t.accent}
          options={['red-blue', 'b&w']}
          onChange={(v) => setTweak('accent', v)} />
      </TweaksPanel>
    </React.Fragment>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
