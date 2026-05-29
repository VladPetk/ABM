// Calm to Camps — design canvas mount.
// Three sections: the intro, the main player (two layout variations), and
// the counterfactual result state. Tweaks let you scrub the player year and
// swap the spotlighted character.

const CC_DEFAULTS = /*EDITMODE-BEGIN*/{
  "year": 2016,
  "character": "Linda"
}/*EDITMODE-END*/;

function App() {
  const [t, setTweak] = useTweaks(CC_DEFAULTS);
  const year = t.year;
  const character = (t.character || 'Linda').toLowerCase();

  return (
    <React.Fragment>
      <DesignCanvas title="Calm to Camps" subtitle="Pedagogical front-end for polarlab · redesign around the 1980–2025 narrative">

        <DCSection id="intro" title="Intro" subtitle="The framing moment before you press play.">
          <DCArtboard id="intro-landing" label="Landing — Calm to Camps" width={1440} height={900}>
            <IntroScreen />
          </DCArtboard>
        </DCSection>

        <DCSection id="player" title="Main player" subtitle="Sidebar right, clean compass, single footer. Scrub year / swap character via Tweaks.">
          <DCArtboard id="player" label="Main player — character right · clean compass · unified footer" width={1440} height={900}>
            <PlayerScreen year={year} character={character} />
          </DCArtboard>
        </DCSection>

        <DCSection id="counterfactual" title="Counterfactual" subtitle="Intervention released 2010 — animated. Hollow = without it, solid = with it; the gap grows as time passes.">
          <DCArtboard id="cf-result" label="Intervention result — Shared neighborhoods & workplaces (animated)" width={1440} height={900}>
            <CounterfactualScreen character={character} />
          </DCArtboard>
        </DCSection>

      </DesignCanvas>

      <TweaksPanel title="Tweaks">
        <TweakSlider label="Player year" value={year} min={1980} max={2025} step={1} onChange={(v) => setTweak('year', v)} />
        <TweakRadio label="Character" value={t.character || 'Linda'}
          options={['Linda', 'James', 'Maria', 'Bob']}
          onChange={(v) => setTweak('character', v)} />
      </TweaksPanel>
    </React.Fragment>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
